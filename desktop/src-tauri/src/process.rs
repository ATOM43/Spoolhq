//! The daemon process the app starts, kept together with its children.
//!
//! The one-file binary is a launcher with the daemon as its child, and the daemon starts
//! agents. On Linux and macOS the launcher gets its own process group, and signals go to
//! the whole group. On Windows it runs inside a Job Object with kill-on-close: closing
//! the job's last handle (the app exiting, or crashing) ends every process in it.

use std::process::{Child, Command};
use std::time::Duration;

/// A started daemon: its launcher process and, on Windows, the job holding it.
pub struct DaemonProcess {
    child: Child,
    #[cfg(windows)]
    job: job::Job,
}

impl DaemonProcess {
    /// Start `command` in its own process group (Unix) or Job Object (Windows).
    pub fn spawn(mut command: Command) -> std::io::Result<Self> {
        #[cfg(unix)]
        {
            use std::os::unix::process::CommandExt;
            command.process_group(0);
        }
        #[cfg(windows)]
        {
            let job = job::Job::new()?;
            let child = command.spawn()?;
            // shortcut: the launcher runs a moment before it joins the job; it unpacks
            // itself for far longer before starting the daemon, so the daemon is inside.
            if let Err(err) = job.assign(&child) {
                let mut child = child;
                let _ = child.kill();
                let _ = child.wait();
                return Err(err);
            }
            Ok(Self { child, job })
        }
        #[cfg(not(windows))]
        Ok(Self {
            child: command.spawn()?,
        })
    }

    /// Whether the launcher has exited (its children may outlive it until [`Self::kill`]).
    pub fn exited(&mut self) -> bool {
        !matches!(self.child.try_wait(), Ok(None))
    }

    /// Ask the whole group to stop (SIGTERM). Windows has no such signal for a console-less
    /// process; there the daemon is asked over `POST /api/shutdown` only.
    pub fn terminate(&mut self) {
        #[cfg(unix)]
        signal_group(self.child.id(), "-TERM");
    }

    /// End the launcher and everything it started, then reap it.
    pub fn kill(&mut self) {
        #[cfg(unix)]
        signal_group(self.child.id(), "-KILL");
        #[cfg(windows)]
        self.job.terminate();
        let _ = self.child.kill();
        let _ = self.child.wait();
    }

    /// Stop gracefully, then kill whatever is left after `wait`.
    pub fn stop(&mut self, wait: Duration) {
        self.terminate();
        let deadline = std::time::Instant::now() + wait;
        while !self.exited() && std::time::Instant::now() < deadline {
            std::thread::sleep(Duration::from_millis(100));
        }
        self.kill();
    }
}

/// Signal the process group led by `pid` with `kill` and an argument list: no shell, and
/// no `libc` or `nix` dependency (decision 455). A group already gone is fine.
#[cfg(unix)]
fn signal_group(pid: u32, signal: &str) {
    let group = format!("-{pid}");
    let _ = Command::new("kill")
        .args([signal, "--", &group])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status();
}

#[cfg(windows)]
mod job {
    use std::os::windows::io::AsRawHandle;
    use std::process::Child;

    use windows_sys::Win32::Foundation::{CloseHandle, HANDLE};
    use windows_sys::Win32::System::JobObjects::{
        AssignProcessToJobObject, CreateJobObjectW, JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION, JobObjectExtendedLimitInformation,
        SetInformationJobObject, TerminateJobObject,
    };

    /// A Job Object with kill-on-close, closed (ending its processes) on drop.
    pub struct Job(HANDLE);

    // The handle is only passed to thread-safe kernel calls.
    unsafe impl Send for Job {}

    impl Job {
        pub fn new() -> std::io::Result<Self> {
            // SAFETY: plain Win32 calls; the handle is checked and owned by `Job`.
            unsafe {
                let handle = CreateJobObjectW(std::ptr::null(), std::ptr::null());
                if handle.is_null() {
                    return Err(std::io::Error::last_os_error());
                }
                let job = Self(handle);
                let mut limits: JOBOBJECT_EXTENDED_LIMIT_INFORMATION = std::mem::zeroed();
                limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
                let size = u32::try_from(size_of::<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>())
                    .expect("the limit struct is small");
                let set = SetInformationJobObject(
                    job.0,
                    JobObjectExtendedLimitInformation,
                    (&raw const limits).cast(),
                    size,
                );
                if set == 0 {
                    return Err(std::io::Error::last_os_error());
                }
                Ok(job)
            }
        }

        pub fn assign(&self, child: &Child) -> std::io::Result<()> {
            // SAFETY: both handles are valid for the duration of the call.
            let done = unsafe { AssignProcessToJobObject(self.0, child.as_raw_handle()) };
            if done == 0 {
                return Err(std::io::Error::last_os_error());
            }
            Ok(())
        }

        pub fn terminate(&self) {
            // SAFETY: the handle is valid until drop.
            unsafe { TerminateJobObject(self.0, 1) };
        }
    }

    impl Drop for Job {
        fn drop(&mut self) {
            // SAFETY: closed once; kill-on-close ends whatever is still in the job.
            unsafe { CloseHandle(self.0) };
        }
    }
}

#[cfg(test)]
mod tests {
    //! A launcher that starts a child, like the one-file binary: the test binary runs
    //! itself as the launcher (`SPOOLHQ_TEST_LAUNCHER=launcher`), which starts itself
    //! again as a sleeping child and prints the child's pid.

    use super::*;
    use std::io::{BufRead, BufReader};
    use std::process::Stdio;

    const ROLE: &str = "SPOOLHQ_TEST_LAUNCHER";

    /// Not a test on its own: the body of the launcher and child processes.
    #[test]
    #[ignore = "run by the process tests as a helper"]
    fn helper_process() {
        match std::env::var(ROLE).as_deref() {
            Ok("launcher") => {
                // Null stdout: the test stops reading the pipe once it has the pid, and
                // libtest's own output into a closed pipe would end the child.
                let mut child = helper("child").stdout(Stdio::null()).spawn().unwrap();
                println!("child-pid={}", child.id());
                let _ = child.wait();
            }
            Ok("child") => std::thread::sleep(Duration::from_secs(60)),
            _ => {}
        }
    }

    fn helper(role: &str) -> Command {
        let mut command = Command::new(std::env::current_exe().unwrap());
        command
            .args(["--exact", "process::tests::helper_process", "--ignored"])
            .args(["--nocapture", "--test-threads=1"])
            .env(ROLE, role)
            .stdin(Stdio::null())
            .stderr(Stdio::null());
        command
    }

    fn start_launcher() -> (DaemonProcess, u32) {
        let mut command = helper("launcher");
        command.stdout(Stdio::piped());
        let mut process = DaemonProcess::spawn(command).unwrap();
        let stdout = process.child.stdout.take().unwrap();
        let pid = BufReader::new(stdout)
            .lines()
            .map_while(Result::ok)
            .find_map(|line| {
                line.split_once("child-pid=")
                    .map(|(_, pid)| pid.trim().to_owned())
            })
            .expect("the launcher prints its child's pid")
            .parse()
            .unwrap();
        assert!(alive(pid), "the child runs");
        (process, pid)
    }

    #[cfg(unix)]
    fn alive(pid: u32) -> bool {
        Command::new("kill")
            .args(["-0", &pid.to_string()])
            .stderr(Stdio::null())
            .status()
            .is_ok_and(|status| status.success())
    }

    #[cfg(windows)]
    fn alive(pid: u32) -> bool {
        use windows_sys::Win32::Foundation::{CloseHandle, WAIT_TIMEOUT};
        use windows_sys::Win32::System::Threading::{
            OpenProcess, PROCESS_SYNCHRONIZE, WaitForSingleObject,
        };
        // SAFETY: plain Win32 calls on a handle closed here.
        unsafe {
            let handle = OpenProcess(PROCESS_SYNCHRONIZE, 0, pid);
            if handle.is_null() {
                return false;
            }
            let running = WaitForSingleObject(handle, 0) == WAIT_TIMEOUT;
            CloseHandle(handle);
            running
        }
    }

    /// The child is gone within 5 s (an orphan is reaped by init a moment later).
    fn gone(pid: u32) -> bool {
        let deadline = std::time::Instant::now() + Duration::from_secs(5);
        while std::time::Instant::now() < deadline {
            if !alive(pid) {
                return true;
            }
            std::thread::sleep(Duration::from_millis(50));
        }
        false
    }

    #[test]
    fn killing_the_daemon_process_ends_the_launchers_child() {
        let (mut process, child) = start_launcher();
        process.kill();
        assert!(process.exited());
        assert!(gone(child), "the launcher's child outlived it");
    }

    #[cfg(unix)]
    #[test]
    fn stop_signals_the_whole_process_group() {
        let (mut process, child) = start_launcher();
        process.stop(Duration::from_secs(5));
        assert!(
            gone(child),
            "the launcher's child outlived the group signal"
        );
    }

    #[cfg(windows)]
    #[test]
    fn closing_the_job_ends_the_launchers_child() {
        let (process, child) = start_launcher();
        // Dropping closes the job's only handle, as when the app exits or crashes.
        drop(process);
        assert!(gone(child), "the launcher's child outlived the job");
    }
}
