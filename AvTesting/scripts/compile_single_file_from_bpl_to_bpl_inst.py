import os
import sys

def is_stub_call(stub_functions, line):
    for function in stub_functions:
        if line.find(function) >= 0:
            return True
    return False

def remove_all_stub_procedures_from_verification(bpl_inst_filepath, stubs_file_path):
    command_output = os.popen("ctags -x --c-types=f "+stubs_file_path).read()
    stub_functions = []
    for line in command_output.splitlines():
        if(line.find("function") >= 0):
            stub_functions.append(line.split(' ')[0])
    print(stub_functions)

    f = open(bpl_inst_filepath)
    line_num = 1
    line_num_list = []
    for line in f.readlines():
        if line.find("call {:AvhEntryPoint}") >= 0:
            print(line)
            if(is_stub_call(stub_functions, line)):
                print("yes", line_num)
                line_num_list.append(line_num)
        line_num = line_num + 1
    f.close()

    if(line_num_list == []):
        return
        
    line_delete_command = "sed -i '"
    for i in range(len(line_num_list)):
        line_delete_command += (str(line_num_list[i]) + "d")
        if(i != len(line_num_list) - 1):
            line_delete_command += ';'

    line_delete_command += ("' " + bpl_inst_filepath)
    print(line_delete_command)
    os.system(line_delete_command)
        # sed -i '2d;5d;8d' file

    



running_file_dir = os.path.dirname(os.path.realpath(__file__))

bpl_filepath = sys.argv[1]
bpl_harness_inst_filepath = bpl_filepath.rsplit('.', 1)[0]+'_inst.bpl'
av_harness_options = "/unknownType:i32 /unknownType:ref"

harness_instrumentation_executable_filepath = "/home/vagrant/smack/corral-av/AddOns/AngelicVerifierNull/AvHarnessInstrumentation/bin/Debug/AvHarnessInstrumentation.exe"
partition_attribute_executable_filepath = "/home/vagrant/smack/corral-av/AddOns/PartitionAttributeAdder/PartitionAttributeAdder/bin/Debug/PartitionAttributeAdder.exe"
inlining_filepath = running_file_dir+"/inline_memory_safety.py"
havoc_delete_filepath = running_file_dir+"/havoc_delete.sh"
macros_filepath = running_file_dir+"/../templates/macrosAsProcedures "
stubs_file_path = running_file_dir +  '/../benchmarks/verisec-benchmarks/suite/lib/stubs.c'
#making sure that all files have executable permissions
os.system("chmod 777 " + inlining_filepath + " " + harness_instrumentation_executable_filepath +" " +partition_attribute_executable_filepath )


#inlining the memory safety function
print("Inlining: python "+inlining_filepath + " " +bpl_filepath+"\n\n")
os.system("python3 "+inlining_filepath + " " +bpl_filepath)

#adding const null
print("echo \"const null:ref;\" >> "+bpl_filepath+"\n\n")
os.system("echo \"const null:ref;\" >> "+bpl_filepath)

# adding the macros
print("Adding macros: cat "+macros_filepath+" >> "+bpl_filepath+"\n\n")
os.system("cat "+macros_filepath+" >> "+bpl_filepath)

#removing the $Alloc[ assertions
print("removing the alloc assertions: sed -i \"/assert .*Alloc/d\" "+bpl_filepath+"\n\n")
os.system("sed -i \"/assert .*Alloc/d\" "+bpl_filepath)

#harness instrumentations
harness_instrumentation_command = harness_instrumentation_executable_filepath + " " + bpl_filepath + " " + bpl_harness_inst_filepath + " " + av_harness_options
print("harness instrumentation: "+harness_instrumentation_command+"\n\n")
os.system(harness_instrumentation_command)

# partition attribute adder
print("partition attribute adder"+partition_attribute_executable_filepath+" " +bpl_harness_inst_filepath +" "+ bpl_harness_inst_filepath+"\n\n")
os.system(partition_attribute_executable_filepath+" " +bpl_harness_inst_filepath +" "+ bpl_harness_inst_filepath )

#make the havoc demonic by removing the angelic keyword from that
command = "bash " + havoc_delete_filepath + " " + bpl_harness_inst_filepath
os.system(command)

#clean
os.system("rm temp_prog.bpl temp_rar.bpl")

#remove the stubs procedures from the verification so it works faster and is easier to analyze
remove_all_stub_procedures_from_verification(bpl_harness_inst_filepath, stubs_file_path)

