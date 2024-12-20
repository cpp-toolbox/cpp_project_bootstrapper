import os
import subprocess
import shutil
from fs_utils.main import attempt_to_delete_files
from user_input.main import get_yes_no, select_options

def get_available_cpp_versions():
    versions = ["98", "03", "11", "14", "17", "20", "23"]
    available_versions = []
    for version in versions:
        result = subprocess.run(
            ["g++", f"-std=c++{version}", "-x", "c++", "-E", "-"],
            input="", capture_output=True, text=True
        )
        if result.returncode == 0:
            available_versions.append(version)
    return available_versions

def select_cpp_version(available_versions):
    print("Available C++ standard versions:")
    for idx, version in enumerate(available_versions):
        print(f"{idx + 1}. C++{version}")
    default_version = available_versions[-1]
    print(f"Press Enter to select the default version: C++{default_version}")
    selection = input("Select a C++ standard version: ")
    if selection.isdigit():
        index = int(selection) - 1
        if 0 <= index < len(available_versions):
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

def create_cmakelists(root_dir, project_name, cmake_version, cpp_version, automatically_find_sources: bool, export_compile_commands: bool, copy_assets_to_build_directory: bool):
    with open(os.path.join(root_dir, "CMakeLists.txt"), "w") as f:


        copy_asset_directory_command = """
        add_custom_target(copy_resources ALL
        COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${PROJECT_SOURCE_DIR}/assets
        ${PROJECT_BINARY_DIR}/assets
        COMMENT "Copying resources into binary directory")
        add_dependencies(${PROJECT_NAME} copy_resources)
        """

        recursively_find_sources_command = """
        file(GLOB_RECURSE SOURCES "src/*.cpp")
        # Add the main executable
        add_executable(${PROJECT_NAME} ${SOURCES})
        """

        main_source_command = "add_executable(${PROJECT_NAME} src/main.cpp)"

        f.write(
            f'cmake_minimum_required(VERSION {cmake_version})\n'
            f'project({project_name})\n\n'
            f'{"set(CMAKE_EXPORT_COMPILE_COMMANDS ON)" if export_compile_commands else ""}\n'
            f'set(CMAKE_CXX_STANDARD {cpp_version})\n\n'
            f'{recursively_find_sources_command if automatically_find_sources else main_source_command}\n'
            f'{copy_asset_directory_command if copy_assets_to_build_directory else ""}'
        )

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
    quick_select = get_yes_no("Before we get started, would you like to choose from a selection of commonly use packages to speed up the process?")

    if quick_select:

        quick_selected_packages = select_options([
                "glfw/3.4",
                "glad/0.1.36",
                "spdlog/1.14.1",
                "glm/cci.20230113",
                "stb/cci.20240531",
                "nlohmann_json/3.11.3",
                "assimp/5.4.3"
                       ])
        packages.extend(quick_selected_packages)

    requries_more_dependencies = True

    if quick_select:
        get_yes_no("Do require further dependencies?")


    if requries_more_dependencies:
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

    first_time_running = get_yes_no("Is it your first time running the boostrapper on this project?")

    if not first_time_running:
        if get_yes_no("Do you want to remove some of the previously boostrapped files? (you will be prompted about what files next)"): 
            programming_files = [ ".clangd", ".clang-format", "CMakeLists.txt", "conanfile.txt"]
            print("What programming related files would you like to delete?") 
            prog_files_to_del = select_options(programming_files) 
            print("Are you prepared to remove these files?", prog_files_to_del) 
            attempt_to_delete_files(prog_files_to_del)

            other_files = [ ".gitignore", "README.md" ]
            print("What other would you like to delete?") 
            other_files_to_delete = select_options(other_files) 
            print("Are you prepared to remove these files?", other_files_to_delete) 
            attempt_to_delete_files(other_files_to_delete)

    root_dir = get_project_root()

    if not os.path.isfile("README.md"):
        project_name = input("Enter the name of your project: ")
        initialize_git_repo(root_dir)

        create_readme_file = get_yes_no("Would you like to create a README.md for your project?")
        if create_readme_file:
            project_description = input("Enter a short description for your project: ")
            create_readme(root_dir, project_name, project_description)

    if os.path.isfile("CMakeLists.txt"):
        print("looks like you have a cmake configuration, if you want to reconfigure, please delete the existing CMakeLists.txt")
    else:
        cmake_version = input("Enter the minimum CMake version (default is 3.10): ") or "3.10"
        available_cpp_versions = get_available_cpp_versions()
        cpp_version = select_cpp_version(available_cpp_versions)
        executable_name = input("What do you want to call your executable? (don't use spaces, use underscores)")
        automatically_find_sources = get_yes_no("Would you like to have source files (.cpp) automatically added as you work?") 
        export_compile_commands = get_yes_no("Would you like to export compile commands? (If you use a language server you want this, otherwise its not needed)")
        copy_assets_to_build_directory = get_yes_no("Do you have an assets directory you'd like to copy to the build directory?")
        
        create_main_cpp(root_dir)
        create_cmakelists(root_dir, executable_name, cmake_version, cpp_version, automatically_find_sources, export_compile_commands, copy_assets_to_build_directory)

    if os.path.isfile("conanfile.txt"):
        print("looks like you're using conan for dependencies, if you would like reconfigure them, delete conanfile.txt")
    else:
        use_conan = get_yes_no("Would you like to use Conan for dependencies?")
        if use_conan:
            create_conanfile(root_dir)

    use_clangd = get_yes_no("Will you be using clangd as a language server?")

    if use_clangd:
        subprocess.run(["python", "scripts/clang_formatting/main.py", "."])

    print("Project setup complete. Next steps:")
    print("conan install .")
    print("copy the output to the cmakelists.txt to link your libs")
    print("cmake --preset conan-release && cmake --build --preset conan-release")
    print("cd build/Release")
    print("you can now run the executable")
    print("consider grabbing some minimal working code here if you're going to do graphics: https://github.com/cpp-toolbox/mwe_glfw/blob/main/src/main.cpp")

if __name__ == "__main__":
    main()
