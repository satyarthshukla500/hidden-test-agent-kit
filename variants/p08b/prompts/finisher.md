No attempt verified a fix. A wrong patch and an empty patch both score zero, so
an applied edit is always better than none. You have at most 5 tool calls.

Issue:
{problem_description}

Last attempt's note: {last_attempt?}

Do NOT reset the working tree: attempt 3 may have left a plausible edit.
1. cd /workspace && git diff --stat     (see whether an edit is already applied)
2. If a source file is already modified: python3 -m py_compile on it; if it
   compiles, call submit_patch now.
3. If nothing is modified: read_file 40 lines around the site named in the note
   (or the best grep -rn hit for the issue's identifiers), then apply the
   smallest change the issue asks for by line numbers:
   python3 - <<'PY'
   p = "PATH"; a, b = START, END
   L = open(p).read().split("\n")
   L[a-1:b] = ["NEW LINE 1", "NEW LINE 2"]
   open(p, "w").write("\n".join(L))
   PY
4. Call submit_patch. Always.
