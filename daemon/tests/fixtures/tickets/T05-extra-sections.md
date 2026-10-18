---
id: T05
title: Extra sections in the body
phase: 1
depends_on: [T02, T03]
status: running
estimate_h: 4
review_required: true
tracker_ref: null
---

Some text before the first heading.

## Scope
- Parse the body without touching it.
  - A nested point.

## Done when
- [ ] First criterion
  with a continuation line
- [x] Second criterion
  - [ ] A nested criterion
* [ ] A star bullet

### Edge cases (still part of Done when)
- [ ] An item under a sub-heading

## Notes

Trailing spaces end this line  
and a hard tab follows:	here.

```markdown
## Done when
- [ ] Not a real item: inside a code fence
```

## Links
- [Design doc](https://example.com/design)
- <https://example.com/issue/5>

[ref]: https://example.com/ref "Reference"
