Every verified fix attempt failed. A wrong patch and no patch both score zero,
so submit the most plausible edit anyway. You have at most 6 tool calls.

Bug report:
{problem_description}

Brief from the analyst (use it for WHERE; never copy its code text):
{bug_brief}

Last attempt's note: {last_attempt?}

1. cd /workspace && git checkout -- . && git clean -fdq
2. read_file the 30-40 lines around the first EDIT_SITE (or around the best
   grep -rn hit for the report's identifiers if the brief names no file).
3. Apply the smallest change that makes the behaviour the report asks for, by
   line numbers from that read_file output:
   python3 - <<'PY'
   p = "PATH"; a, b = START, END
   L = open(p).read().split("\n")
   L[a-1:b] = ["NEW LINE 1", "NEW LINE 2"]
   open(p, "w").write("\n".join(L))
   PY
4. python3 -m py_compile PATH. If it fails, fix the syntax once.
5. Call submit_patch. Always.
