import os import subprocess import shutil

    def get_available_cpp_versions() :versions =["98", "03", "11", "14", "17", "20", "23"] available_versions =[] for version in versions:result = subprocess.run(["g++", f "-std=c++{version}", "-x", "c++", "-E", "-"], input = "", capture_output = True, text = True) if result.returncode == 0 :available_versions.append(version) return available_versions

                                                                                                                                                                   def select_cpp_version(available_versions) :print("Available C++ standard versions:") for idx, version in enumerate(available_versions) :print(f "{idx + 1}. C++{version}") default_version = available_versions[- 1] print(f "Press Enter to select the default version: C++{default_version}") selection = input("Select a C++ standard version: ") if selection.isdigit() :index = int(selection) - 1 if 0 <= index < len(available_versions):
            return available_versions[index]
    return default_version

def get_project_root():
    current_dir = os.getcwd()
    print(f"The current directory is: {current_dir}")
    root_dir = input(f"Enter the project root directory (default is current directory): ").strip()
    if not root_dir:
        root_dir = current_dir
    elif not os.path.isabs(root_dir):
        root_dir = os.path.abspath(root_dir)
    if not os.path.exists(root_dir):
        os.makedirs(root_dir)
    return root_dir

def create_main_cpp(root_dir):
    src_dir = os.path.join(root_dir, "src")
    os.makedirs(src_dir, exist_ok=True)
    with open(os.path.join(src_dir, "main.cpp"), "w") as f:
        f.write(
            '#include <iostream>\n\n'
            'int main() {\n'
            '    std::cout << "Hello, World!" << std::endl;\n'
            '    return 0;\n'
            '}\n'
        )
    print(f"Created src/main.cpp in {root_dir} with a 'Hello, World!' program.")

def create_cmakelists(root_dir, project_name, cmake_version, cpp_version, export_compile_commands):
    with open(os.path.join(root_dir, "CMakeLists.txt"), "w") as f:
        f.write(
            f'cmake_minimum_required(VERSION {cmake_version})\n'
            f'project({project_name})\n\n'
            f'set(CMAKE_CXX_STANDARD {cpp_version})\n\n'
            'add_executable(${PROJECT_NAME} src/main.cpp)\n'
        )
        if export_compile_commands:
            f.write('set(CMAKE_EXPORT_COMPILE_COMMANDS ON)\n')
    print(f"Created CMakeLists.txt in {root_dir}.")

def create_readme(root_dir, project_name, project_description):
    with open(os.path.join(root_dir, "README.md"), "w") as f:
        f.write(f"# {project_name}\n\n{project_description}\n")
    print(f"Created README.md in {root_dir}.")

def search_conan_package(package_name):
    print(f"Searching for package '{package_name}' in conan center...")
    subprocess.run(["conan", "search", package_name, "-r", "conancenter"])

def create_conanfile(root_dir):
    packages = []
    print("Conan package management:")
    print("Use 'search <package>' to search for packages.")
    print("Use 'add <package/version>' to add a package to your project.")
    print("Use 'remove <package/version>' to remove a package from your project.")
    print("Type 'done' when you are finished.")

    while True:
        user_input = input("> ").strip()
        if user_input.lower() == "done":
            break
        elif user_input.startswith("search "):
            package_name = user_input[len("search "):].strip()
            if package_name:
                search_conan_package(package_name)
        elif user_input.startswith("add "):
            package = user_input[len("add "):].strip()
            if package and package not in packages:
                packages.append(package)
                print(f"Added package '{package}'")
        elif user_input.startswith("remove "):
            package = user_input[len("remove "):].strip()
            if package in packages:
                packages.remove(package)
                print(f"Removed package '{package}'")
        else:
            print("Invalid command. Please use 'search', 'add', 'remove', or 'done'.")

    if packages:
        with open(os.path.join(root_dir, "conanfile.txt"), "w") as f:
            f.write("[requires]\n")
            for package in packages:
                f.write(f"{package}\n")
            f.write("\n[generators]\nCMakeDeps\nCMakeToolchain\n\n[layout]\ncmake_layout")
        print(f"Created conanfile.txt in {root_dir} with the following packages:")
        for package in packages:
            print(f" - {package}")
    else:
        print("No packages were added. Skipping conanfile.txt creation.")

def is_git_repo(path):
    return subprocess.run(["git", "-C", path, "rev-parse"], capture_output=True).returncode == 0

def initialize_git_repo(root_dir):
    if not is_git_repo(root_dir):
        print("The project root directory is not a git repository.")
        if input("Would you like to initialize a git repository here? (y/N): ").strip().lower() == "y":
            subprocess.run(["git", "init", root_dir])
            print(f"Initialized an empty git repository in {root_dir}")

def add_git_submodule(root_dir, url, name):
    if input(f"Would you like to add {name} as a git submodule? (y/N): ").strip().lower() == "y":
        subprocess.run(["git", "-C", root_dir, "submodule", "add", url])
        print(f"Added {name} as a git submodule.")

def main():
    print("Welcome to the C++ Project Bootstrapper!")
    print("You can press Enter to accept the default value for any prompt.")

    root_dir = get_project_root()

    project_name = input("Enter the name of your project: ")

    initialize_git_repo(root_dir)

    create_readme_file = input("Would you like to create a README.md for your project? (y/N): ").strip().lower() == "y"
    if create_readme_file:
        project_description = input("Enter a short description for your project: ")
        create_readme(root_dir, project_name, project_description)

    cmake_version = input("Enter the minimum CMake version (default is 3.10): ") or "3.10"
    available_cpp_versions = get_available_cpp_versions()
    cpp_version = select_cpp_version(available_cpp_versions)
    export_compile_commands = input("Would you like to export compile commands? (y/N): ").strip().lower() == "y"

    create_main_cpp(root_dir)
    create_cmakelists(root_dir, project_name, cmake_version, cpp_version, export_compile_commands)

    use_conan = input("Would you like to use Conan for dependencies? (y/N): ").strip().lower() == "y"
    if use_conan:
        create_conanfile(root_dir)

    add_git_submodule(root_dir, "git@github.com:cpp-toolbox/clang_formatting.git", "clang_formatting")
    add_git_submodule(root_dir, "git@github.com:cpp-toolbox/sbpt.git", "sbpt")

    self_delete = input("Would you like this script to delete itself after setup? (y/N): ").strip().lower() == "y"
    if self_delete:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Deleting {script_dir}...")
        shutil.rmtree(script_dir)

    print("Project setup complete!")

if __name__ == "__main__":
    main()
