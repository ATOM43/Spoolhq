import ReactMarkdown, { defaultUrlTransform } from "react-markdown";

/**
 * Untrusted markdown (specs, tickets, agent text) as React elements. Raw HTML is
 * dropped (`skipHtml`), never parsed; link and image URLs go through react-markdown's
 * transform, which empties anything but http(s), mailto, tel and relative URLs, so
 * `javascript:` can't run. No `dangerouslySetInnerHTML` anywhere.
 */
export function Markdown({ source }: { source: string }) {
  return (
    <div className="markdown text-sm">
      <ReactMarkdown
        skipHtml
        urlTransform={defaultUrlTransform}
        components={{
          // The app has no opener: a click would navigate the webview away.
          a: ({ href, children }) => (
            <a
              href={href}
              title={href}
              onClick={(event) => {
                event.preventDefault();
              }}
            >
              {children}
            </a>
          ),
        }}
      >
        {source}
      </ReactMarkdown>
    </div>
  );
}
