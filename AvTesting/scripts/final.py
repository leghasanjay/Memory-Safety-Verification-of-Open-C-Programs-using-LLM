import os
import requests
import subprocess

url = "http://172.27.21.156:11434/api/generate"
API_KEY = "YOUR_KEY"

# -------------------- UTIL --------------------
def read_file(file):
    with open(file, "r") as f:
        return f.read()

# -------------------- EXTRACT PROCEDURE --------------------
def extract_procedure(bpl_code):
    lines = bpl_code.split("\n")
    start = -1
    brace_count = 0
    inside = False
    started_brace = False

    for i, line in enumerate(lines):
        if "procedure {:entrypoint}" in line:
            start = i
            inside = True

        if inside:
            if "{" in line:
                started_brace = True

            if started_brace:
                brace_count += line.count("{")
                brace_count -= line.count("}")

                if brace_count == 0:
                    return "\n".join(lines[start:i+1])

    return ""

# -------------------- CORRAL --------------------
def run_corral(bpl_file):
    result = subprocess.run(
        ["corral", bpl_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    print(result.stdout)
    return result.stdout

# -------------------- INJECTION --------------------
def inject_assumptions_into_bpl(full_bpl_code, assumptions, output_file):
    lines = full_bpl_code.splitlines(keepends=True)
    new_lines = []
    inserted = False

    for line in lines:
        new_lines.append(line)

        if (not inserted) and "call $initialize();" in line:
            for a in assumptions:
                new_lines.append("  " + a.strip() + "\n")
            inserted = True

    with open(output_file, "w") as f:
        f.writelines(new_lines)

    return output_file

# -------------------- STEP 1: TEXT ASSUMPTIONS --------------------
def generate_text_assumptions(c_code):
    prompt = f"""
You are an expert in memory-safety verification of C programs.
An open program is a program whose environment is not known to us. For example, we have a function but do not have any information about the caller of this function. In this situation, it is difficult to say whether the program is buggy w.r.t. memory safety violations like buffer overflow or buffer overread. Since we do not have any information about the environment where the function will be executed we make some idiomatic assumptions about the environment (i.e. what is the common practice about the environment when calling these functions, for example, when calling strlen(char* str), it is assumed that the function will always be called in an environment where str should not points to NULL and should be within the range of the buffer). If by generating such idiomatic assumptions we are able to verify an open program but without these assumptions the open program violates memory safety (like causing buffer overflow or buffer overread) then we say that it is a false positive. But if we are not able to verify the program even after making these idiomatic assumptions about the environment then we say that the program contains actual bug and it is a true positive. Now, I want you to generate appropriate idiomatic assumptions for the following function such that it does not violate any memory safety property.

Your task:
Given the following C function, generate only the idiomatic assumptions about the environment to ensure memory safety (no buffer overflow or buffer overread).

Rules:
- Output only assumptions in plain English (not Boogie).
- Each assumption must be on a new line.
- Do not include numbering, bullets, explanations, or extra text.
- Do not repeat assumptions.
- Keep assumptions precise and minimal (avoid unnecessary ones).

Focus on:
- Pointer validity (non-null)
- Valid allocated memory regions
- Buffer size bounds
- Null-termination (if applicable)
- Safe indexing and loop bounds



C code:
{c_code}

"""

    response = requests.post(
        url,
        json={"model": "qwen2.5-coder:latest", "prompt": prompt, "stream": False}
    )

    output = response.json().get("response", "")

    return [line.strip() for line in output.split("\n") if line.strip()]

# -------------------- STEP 2: BOOGIE ASSUMPTIONS --------------------
def generate_boogie_assumptions(c_code, bpl_code, text_assumptions):

    prompt = f"""
You are converting plain-English memory-safety assumptions into Boogie code for a SMACK-generated procedure.

Task:
Given the C code, the plain-text assumptions, and the Boogie procedure, output only valid Boogie assume statements that can be pasted directly into the procedure.

Rules:
- Output only Boogie assume lines.
- Each assumption must be on its own line.
- Do not output markdown, bullets, numbering, comments, explanations, or extra text.
- Use only variables that appear in the given Boogie procedure.
- Do not invent new variables, functions, or predicates.
- Do not use any undeclared function names.
- If a text assumption cannot be translated safely using only the variables and functions already present in the procedure, omit it.
- Do not repeat assumptions.
- Keep the output minimal and syntax-correct.

Important:
- Every line must start with `assume`.
- Every assumption must end with `;`
- Use exactly the same variable names as in the procedure.
- If the procedure contains pointer variables like `$p0`, `$p1`, `$p2`, use those names exactly.
- Do not output any assumption that would introduce a syntax error in Boogie.

Example:
Text assumptions:
- input pointer is non-null
- buffer is allocated
- pointer lies within allocated buffer

Valid Boogie output:
assume $p0 != 0; 
assume $Alloc[$base($p0)]; 
assume $sle.ref.bool($base($p0), $p0); 
assume $sle.ref.bool( $add.ref($p0, $i2p.i64.ref(1)), $add.ref($base($p0), $Size($base($p0))) );
 
Your previour wrong outputs which causes error-->
1.-->
Generated Assumptions:
assume {{:sourceloc "filename.c", line_number, column_number}} true;
assume {{:verifier.code 0}} true;
[+] Modified BPL written to: strlen_strlen_inst.bpl
Corral program verifier version 1.1.8.0
Warning: Using default recursion bound of 1
strlen_strlen_inst.bpl(1513,35): Error: undeclared identifier: line_number
strlen_strlen_inst.bpl(1513,48): Error: undeclared identifier: column_number
2 name resolution errors in strlen_strlen_inst.bpl
Unhandled exception. cba.Util.InvalidProg: Cannot resolve strlen_strlen_inst.bpl
   at cba.Util.BoogieUtil.ReadAndOnlyResolve(String filename) in /home/runner/work/corral/corral/source/Util/BoogieUtil.cs:line 439
   at cba.Driver.GetInputProgram(Configs config) in /home/runner/work/corral/corral/source/Corral/Driver.cs:line 568
   at cba.Driver.run(String[] args) in /home/runner/work/corral/corral/source/Corral/Driver.cs:line 233
   at cba.Driver.Main(String[] args) in /home/runner/work/corral/corral/source/Corral/Driver.cs:line 44

2.-->
Generated Assumptions:
assume {{:sourceloc "small.c", 5, 5}} true;
assume {{:verifier.code 0}} true;
assume {{:sourceloc "small.c", 5, 11}} true;
assume $p0 != 0;
assume $Alloc[$base($p0)];
assume $sle.ref.bool($base($p0), $p0);
assume $sle.ref.bool( $add.ref($p0, $i2p.i64.ref(strlen)), $add.ref($base($p0), $Size($base($p0))) );
assume {{:sourceloc "small.c", 6, 5}} true;

[+] Modified BPL written to: strlen_strlen_inst.bpl
Corral program verifier version 1.1.8.0
Warning: Using default recursion bound of 1
Single threaded program detected
Verifying program while tracking: {{assertsPassed}}
Program has a potential bug: False bug
Verifying program while tracking: {{assertsPassed, $Alloc}}
Program has a potential bug: True bug
PersistentProgram(6443,1): error PF5001: This assertion can fail

strlen_strlen_inst.bpl(16101,1): error PF5001: This assertion can fail

Execution trace:
(1,0)     strlen_strlen_inst.bpl(16101,3): anon0  (ASSERTION FAILS assert {{:valid_deref}} $sle.ref.bool($add.ref(p, size), $add.ref($base(p), $Size($base(p))));
 )
(1,0)    strlen_strlen_inst.bpl(1543,3): $bb1  (RETURN from __SMACK_check_memory_safety )
(1,0)    strlen_strlen_inst.bpl(1543,3): $bb1  (Done)

3.-->
Generated Assumptions:
assume $p0 != 0;
assume $Alloc[$base($p0)];
assume $sle.ref.bool($base($p0), $p0);
assume $sle.ref.bool( $add.ref($p0, $i2p.i64.ref(1)), $add.ref($base($p0), $Size($base($p0))) );

[+] Modified BPL written to: strlen_strlen_inst.bpl
Corral program verifier version 1.1.8.0
Warning: Using default recursion bound of 1
strlen_strlen_inst.bpl(1516,51): Error: undeclared identifier: size
1 name resolution errors in strlen_strlen_inst.bpl
Unhandled exception. cba.Util.InvalidProg: Cannot resolve strlen_strlen_inst.bpl

4.-->
Generated Assumptions:
assume {{:sourceloc "small.c", 5, 5}} true;
assume {{:verifier.code 0}} true;
assume {{:sourceloc "small.c", 5, 11}} true;
assume $p0 != 0;
assume $Alloc[$base($p0)];
assume $sle.ref.bool($base($p0), $p0);
assume $sle.ref.bool( $add.ref($p0, $i2p.i64.ref(strlen)), $add.ref($base($p0), $Size($base($p0))) );

[+] Modified BPL written to: strlen_strlen_inst.bpl
Corral program verifier version 1.1.8.0
Warning: Using default recursion bound of 1
strlen_strlen_inst.bpl(1518,51): Error: undeclared identifier: size
1 name resolution errors in strlen_strlen_inst.bpl
Unhandled exception. cba.Util.InvalidProg: Cannot resolve strlen_strlen_inst.bpl

5.-->
Generated Assumptions:
assume $p0 != null;
assume $i1 >= 1;

STRICT HARD CONSTRAINTS (MUST FOLLOW):
1. You MUST use ONLY variables that appear EXACTLY in the given Boogie procedure.
2. If a variable is not present in the procedure, DO NOT use it.
3. DO NOT invent constants like MAX_STRING_LEN, size, length, null etc.
4. DO NOT use functions like ref(...), i2p.i64(...), or any undeclared function.
5. If you cannot express an assumption using ONLY the given variables, SKIP that assumption.

CRITICAL:
- If you violate any rule, the output becomes INVALID and unusable.
- It is better to output FEWER assumptions than incorrect ones.

OUTPUT FORMAT:
Only valid Boogie assume statements.
Nothing else.
  
    c code
    {c_code}
    
    Plain-text assumptions:
    {text_assumptions}

    Boogie procedure:
    {bpl_code}

"""

    response = requests.post(
        url,
        json={"model": "qwen2.5-coder:latest", "prompt": prompt, "stream": False}
    )

    output = response.json().get("response", "")

    assumptions = []
    for line in output.split("\n"):
        line = line.strip()
        if line.startswith("assume"):
            if not line.endswith(";"):
                line += ";"
            assumptions.append(line)

    return list(dict.fromkeys(assumptions))