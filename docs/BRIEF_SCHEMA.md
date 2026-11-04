# bug_brief schema

Analyzer writes `bug_brief` to session state. Coder interpolates it. Every field
mandatory; literal NONE when empty.

| Field | Constraint |
|---|---|
| FAILING_TEST | node id, or NO_TEST |
| TRACEBACK | innermost 3 non-test frames, verbatim |
| FILES | path:start-end, 1-3 entries |
| CODE | 5-20 verbatim lines each, 2 lines of context |
| DIAGNOSIS | 2 sentences naming the wrong value or missing branch |
| EDIT_SITES | confidence order, each with an exact old_string |
| RISK | call sites, or NONE |

Verbatim is the point. A paraphrased old_string costs a re-read and often the
task.
