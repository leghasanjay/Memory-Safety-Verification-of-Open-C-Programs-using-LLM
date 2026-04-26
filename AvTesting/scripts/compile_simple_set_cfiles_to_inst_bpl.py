import os
import subprocess

from final import (
    read_file,
    extract_procedure,
    generate_text_assumptions,
    generate_boogie_assumptions,
    inject_assumptions_into_bpl,
    run_corral
)

def read_all_simple_set_files(file):
    with open(file) as f:
        return [line.strip() for line in f if line.strip()]

# -------------------- GET FILE LIST --------------------
cwd = os.getcwd()
os.chdir('../benchmarks/verisec-benchmarks/suite/programs/apps/')
all_files = subprocess.check_output('perl build_master_list.pl', shell=True).decode()
os.chdir(cwd)

# -------------------- PATHS --------------------
c_to_bpl_compile_file = os.path.abspath("compile_single_file_from_c_to_bpl.py")
bpl_to_bpl_inst_compile_file = os.path.abspath("compile_single_file_from_bpl_to_bpl_inst.py")
stubs_file_path = os.path.abspath('../benchmarks/verisec-benchmarks/suite/lib/stubs.c')

simple_set_files = read_all_simple_set_files("programs_to_run_on")

# -------------------- RESULTS STORAGE --------------------
results = []

number = 0

# -------------------- MAIN LOOP --------------------
for files in all_files.split('\n'):

    if files.strip() == "":
        continue

    c_filepath = files.split(' ')[0]

    if not (os.path.abspath(c_filepath) in [os.path.abspath(f) for f in simple_set_files]):
        continue

    number += 1
    print("\n==============================")
    print("Processing:", c_filepath)

    workdir = os.path.dirname(c_filepath)
    os.chdir(workdir)

    # CLEAN OLD FILES
    for f in os.listdir():
        if f.endswith(".bpl") or f.endswith("_inst.bpl"):
            try:
                os.remove(f)
            except:
                pass

    try:
        # -------------------- SMACK --------------------
        file_list = files.split(' ')
        file_list.append(stubs_file_path)
    
        cmd = "python3 " + c_to_bpl_compile_file + " " + ":".join(file_list)
        subprocess.run(cmd, shell=True)

        base_name = os.path.basename(c_filepath).split('.')[0]

        bpl_files = [f for f in os.listdir() if f.startswith(base_name) and f.endswith(".bpl")]

        if not bpl_files:
            print("❌ BPL not created")
            results.append((c_filepath, "ERROR"))
            continue

        bpl_file = bpl_files[0]
        print("✔ BPL:", bpl_file)

        # -------------------- LLM STEP --------------------
        c_code = read_file(c_filepath)
        bpl_full = read_file(bpl_file)
        proc = extract_procedure(bpl_full)

        text_assumptions = generate_text_assumptions(c_code)
        boogie_assumptions = generate_boogie_assumptions(c_code, proc, "\n".join(text_assumptions))

        if not boogie_assumptions or len(boogie_assumptions) < 3:
            print("⚠️ Weak/invalid LLM assumptions → using fallback")
            boogie_assumptions = [
                "assume $p0 != 0;",
                "assume $Alloc[$base($p0)];",
                "assume $sle.ref.bool($base($p0), $p0);",
                "assume $sle.ref.bool($add.ref($p0, $i2p.i64.ref(1)), $add.ref($base($p0), $Size($base($p0))));"
            ]

        print("TEXT:", text_assumptions)
        print("BOOGIE:", boogie_assumptions)

        if not boogie_assumptions:
            print("⚠️ LLM failed → using fallback assumptions")
            boogie_assumptions = [
                "assume $p0 != 0;",
                "assume $Alloc[$base($p0)];",
                "assume $sle.ref.bool($base($p0), $p0);"
            ]

        llm_bpl = bpl_file.replace(".bpl", "_llm.bpl")
        inject_assumptions_into_bpl(bpl_full, boogie_assumptions, llm_bpl)

        # -------------------- INSTRUMENT --------------------
        cmd2 = "python3 " + bpl_to_bpl_inst_compile_file + " " + llm_bpl
        subprocess.run(cmd2, shell=True)

        inst_file = llm_bpl.replace(".bpl", "_inst.bpl")

        if not os.path.exists(inst_file):
            print("❌ inst not created")
            results.append((c_filepath, "ERROR"))
            continue

        # -------------------- CORRAL --------------------
        print("Running Corral...")
        corral_output = run_corral(inst_file)
        print(f"[{number}] Done: {c_filepath}")

        # -------------------- CLASSIFICATION --------------------
        if "Program has no bugs" in corral_output:
            result = "SAFE"
        elif "True bug" in corral_output:
            result = "BUG"
        else:
            result = "UNKNOWN"

        print("RESULT:", result)
        results.append((c_filepath, result))

    except Exception as e:
        print("❌ ERROR:", str(e))
        results.append((c_filepath, "ERROR"))

    print("✔ done:", number)

# -------------------- SAVE RESULTS --------------------
output_file = os.path.abspath("benchmark_results.csv")

with open(output_file, "w") as f:
    f.write("file,result\n")
    for file, res in results:
        f.write(f"{file},{res}\n")

# -------------------- SUMMARY --------------------
safe = sum(1 for _, r in results if r == "SAFE")
bug = sum(1 for _, r in results if r == "BUG")
error = sum(1 for _, r in results if r == "ERROR")
unknown = sum(1 for _, r in results if r == "UNKNOWN")

print("\n==============================")
print("FINAL SUMMARY")
print("==============================")
print("Total:", len(results))
print("SAFE:", safe)
print("BUG:", bug)
print("ERROR:", error)
print("UNKNOWN:", unknown)

print("\nResults saved to:", output_file)