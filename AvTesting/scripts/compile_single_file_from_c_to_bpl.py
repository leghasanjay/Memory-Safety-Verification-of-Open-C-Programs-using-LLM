import os
import sys

def get_entry_points(c_filepath):
    command_output = os.popen("ctags -x --c-types=f "+c_filepath).read()
    print(command_output)
    entry_points = [line.split(' ')[0] for line in command_output.split('\n') if not(line.split(' ')[0] == 'main')]
    #entry_points = [line.split(' ')[0] for line in command_output.split('\n') if (line.split(' ')[0] == 'main')]
    if(entry_points == ['']):
        #main was the only entrypoint
        #add main to the list of entrypoints
        #f = open("withoutMainFiles", "a+")
        #f.write(c_filepath+"\n")
        #f.close()
        entry_points = [line.split(' ')[0] for line in command_output.split('\n')]
    print("entry_points")
    print(entry_points)
    f = open("/home/vagrant/smack/AvTesting/scripts/allFiles", "a+")
    f.write(c_filepath+"\n")
    if len(entry_points)>2:
        for val in entry_points:
            f.write(val+"\n")
    f.write("\n\n")
    f.close()
    return entry_points 

n = len(sys.argv)
if(n != 2):
    print("less arguments : usage : python compilation.py 'cfile1:cfile2:cfile3'")
    exit()

#get all the c files required for the compilation
c_files = ' '.join((sys.argv[1]).split(':'))
#c_filepath is the first file or the file with the main method
c_filepath = ((sys.argv[1]).split(':'))[0]
#get all the entrypoints except main since we want to compoile without harnesses
entrypoint_function_names = get_entry_points(c_filepath)
print(" the entrypoints are:", entrypoint_function_names)
#exit()
bpl_filepath = c_filepath.rsplit('.', 1)[0]+'.bpl'
smack_options = "--no-verify --check valid-deref --clang-options=\'-fno-builtin\'"

#exit()
#f1 = open("/home/vagrant/smack/AvTesting/scripts/bplFiles","w+")
#f1.write("")
#f1.close()
# #compiling to bpl
for funcName in entrypoint_function_names:
    if len(funcName)<2:
        continue
    smack_compilation_command =  "smack " + smack_options + "  --entry-points " + funcName + " -bpl "+bpl_filepath[:-4] +"_"+ funcName+".bpl" + " " + c_files
    #smack_compilation_command =  "smack " + smack_options + " -bpl "+bpl_filepath + " " + c_files
    print("\n\nsmack command: "+smack_compilation_command+"\n\n")
    os.system(smack_compilation_command)
    f1 = open("/home/vagrant/smack/AvTesting/scripts/bplFiles","a+")
    f1.write(c_filepath.rsplit('.', 1)[0]+"_"+funcName+".bpl\n")
    f1.close()
    f1 = open("/home/vagrant/smack/AvTesting/scripts/bplFilesinst","a+")
    f1.write(c_filepath.rsplit('.', 1)[0]+"_"+funcName+"_inst.bpl\n")
    f1.close()
