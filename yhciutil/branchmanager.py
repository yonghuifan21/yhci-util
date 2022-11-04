import os
import shutil
import ruamel.yaml
import datetime
from git import Repo
import logging


# yaml 数据模型
class YamlModuleModel:
    module = ''
    pod = ''
    version = ''
    git = ''
    branch = ''
    tag = ''
    path = ''
    new_tag = ''
    configurations = ''
    inhibit_warnings = False

    def __init__(self, module, pod, version, git, branch, tag, path, newtag, configurations, inhibit_warnings):
        self.module = module
        self.pod = pod
        self.git = git
        self.branch = branch
        self.tag = tag
        self.path = path
        self.new_tag = newtag
        self.configurations = configurations
        self.inhibit_warnings = inhibit_warnings


# 输出合并结果，如果result = 1 表示成功，result = 0 表示失败
class YamlBranchModel:
    module = ''
    result = 0

    def __init__(self, module, res):
        self.module = module
        self.result = res


# 读取yaml文件数据
def yaml_data(yaml_path):
    with open(yaml_path, 'r') as y:
        yaml = ruamel.yaml.YAML()
        temp_yaml = yaml.load(y.read())
        return temp_yaml


# 写入文件
def update_yaml(yaml_path, data):
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml = ruamel.yaml.YAML()
        yaml.dump(data, f)


# 加载yml文件
def load_yaml(data):
    convertDepList = []
    for i in range(0, len(data)):
        cur_dep = data[i]
        module = YamlModuleModel(module=cur_dep.get("module", None),
                                 pod=cur_dep["pod"],
                                 version=cur_dep.get("version", None),
                                 git=cur_dep.get("git", None),
                                 branch=cur_dep.get("branch", None),
                                 tag=cur_dep.get("tag", None),
                                 path=cur_dep.get("path", None),
                                 newtag=cur_dep.get("newtag", None),
                                 configurations=cur_dep.get("configurations", None),
                                 inhibit_warnings=cur_dep.get("inhibit_warnings", False)
                                 )
        convertDepList.append(module)

    return convertDepList


# 清空文件夹及目录
def del_file(path_data):
    # os.listdir(path_data)#返回一个列表，里面是当前目录下面的所有东西的相对路径
    shutil.rmtree(path_data)


# 获取所有的分支
def get_branches(project_dir):
    repo = Repo(project_dir, search_parent_directories=True)
    branch_list = repo.branches
    return branch_list


# 基于master 和 f_tag，创建一个新的分支new_branch，如果存在仓库则先清空仓库，再拉取分支
# 1. 清空当前工作目录
# 2. 拉取代码
# 3. 新建分支
# 4. 推送分支
def auto_create_branch(filepath, git, f_branch, f_tag, n_branch):
    # 创建分支
    create_file(filepath)
    return new_branch(filepath, git, f_branch, f_tag, n_branch)


# 新建分支
def new_branch(filepath, git, f_branch, f_tag, n_branch):
    pull_branch = f_branch
    if not (f_branch and len(f_branch) > 0):
        pull_branch = "master"
    if f_branch and len(f_branch) > 0 and f_branch == n_branch:
        pull_branch = "master"
    # clone 代码
    git_clone_command = "git clone -b " + pull_branch + " " + git + " " + filepath
    # 创建一个新分支
    git_create_branch = "git branch " + n_branch
    if f_tag and len(f_tag) > 0:
        git_create_branch += " " + f_tag
    # checkout
    git_checkout_command = "git checkout " + n_branch
    # git push
    git_push_command = "git push origin " + n_branch
    create_status = 0
    create_status += os.system(git_clone_command)
    logging.info("执行 " + git_clone_command)
    # master分支下的版本号
    branchs = get_branches(filepath)
    if n_branch in branchs:
        os.system(git_checkout_command)
        logging.info(n_branch + "分支已存在")
        return ""
    os.chdir(filepath)
    create_status = os.system(git_create_branch)
    create_status += os.system(git_checkout_command)
    logging.info("新分支已经提交到master")
    create_status += os.system(git_push_command)
    if not create_status == 0:
        logging.warning("新分支创建失败")
        return ""
    return n_branch


# 基于master 和 f_tag，创建一个新的分支new_branch, 如果文件目录存在，则判断当前是否在dui'y
# 1. 清空当前工作目录
# 2. 拉取代码
# 3. 新建分支
# 4. 推送分支q1`
def auto_update_branch(filepath, git, f_branch, f_tag, n_branch):
    _branch = f_branch
    if not (f_branch and len(f_branch) > 0):
        _branch = "master"
    # 创建分支
    if os.path.exists(filepath):
        # 存在目录，判断当前处于哪个分支下
        try:
            repo = Repo(filepath)
        except:
            br = new_branch(filepath, git, _branch, f_tag, n_branch)
            return br
        c_branch = repo.head
        repo.index.add(items=[])
        repo.index.commit("commit")
        # 判断当前分支是不是是指定的开发分支
        if c_branch == f_branch:
            remote = repo.remote()
            remote.pull()
        else:
            branchlist = repo.branches
            git = repo.git
            if n_branch in branchlist:
                # 存在远端分支
                # 切换到对应分支
                repo.git.checkout(n_branch)
            else:
                # 不存在分支
                # 新建一个分支
                git.branch(n_branch)
                # 切换到对应分支
                repo.git.checkout(n_branch)
        return n_branch
    else:
        create_file(filepath)
        br = new_branch(filepath, git, _branch, f_tag, n_branch)
        return br


# 基于master 和 f_tag，创建一个新的分支new_branch
# 1. 清空当前工作目录
# 2. 拉取代码
# 3. 新建分支
# 4. 推送分支
def auto_delete_branch(filepath, git, f_branch, f_tag, n_branch):
    # 创建分支
    create_file(filepath)
    f_branch = f_branch
    if not (f_branch and len(f_branch) > 0):
        f_branch = "master"
    # clone 代码
    git_clone_command = "git clone -b " + f_branch + " " + git + " " + filepath

    # 创建一个新分支 origin/dev-20221101-8
    git_delete_branch = "git branch -D " + "dev-20221101-8"

    # git push
    git_push_command = "git push origin --delete " + "dev-20221101-8"
    os.system(git_clone_command)
    logging.info("执行 " + git_clone_command)
    # master分支下的版本号
    os.chdir(filepath)
    os.system("pwd")
    os.system("ls")
    logging.info("新分支已经提交到master")
    os.system(git_push_command)


# 基于主项目分支切一个新的分支
def checkout_project(filepath, git, c_branch, c_tag, n_branch):
    # return
    # 进入模块
    # clone 代码
    c_branch = c_branch
    if not (c_branch and len(c_branch) > 0):
        c_branch = "master"

    git_clone_command = "git clone -b " + c_branch + " " + git + " " + filepath
    # 创建一个新分支
    git_create_branch = "git branch " + n_branch
    if c_tag and len(c_tag) > 0:
        git_create_branch += c_tag
    # checkout
    git_checkout_command = "git checkout " + n_branch
    # 推送分支
    git_push_branch = "git push origin " + n_branch
    logging.info(git_clone_command)
    # Repo.clone_from(git, to_path=filepath, branch=c_branch)
    # os.chdir(filepath)
    clone_status = os.system(git_clone_command)
    logging.info(clone_status)
    os.system(git_create_branch)
    os.system(git_checkout_command)
    os.system(git_push_branch)


# 清空或者创建一个新的目录
def create_file(path):
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        del_file(path)
        os.makedirs(path)


# 基于podfileModule来给每个组件创建一个分支
def create_branch(module_list, module_f_path, n_branch, exception_modules, c_path):
    index = 0
    create_branch_result = []
    for a in module_list:
        if ((a.branch and len(str(a.branch)) > 0) or (a.tag and len(str(a.tag)) > 0)) and (
                a.module not in exception_modules):
            filename = a.module
            module_path = module_f_path + filename + "/"
            branch_name = auto_create_branch(module_path, a.git, a.branch, a.tag, n_branch)
            res = 1
            if not (branch_name and len(branch_name) > 0):
                logging.info("自动创建分支失败 ++++" + a.pod)
                res = 0
            new_branch_model = YamlBranchModel(a.module, res)
            create_branch_result.append(new_branch_model)
        index += 1
        os.chdir(c_path)
    return create_branch_result


# 基于podfileModule来给每个组件更新到新分支
def update_branch(module_list, module_f_path, n_branch, exception_modules, c_path, f_branch):
    index = 0
    create_branch_result = []
    for a in module_list:
        if not (a.branch and len(a.branch) > 0):
            a.branch = f_branch
        if ((a.branch and len(a.branch) > 0) or (a.tag and len(a.tag) > 0)) and (
                a.module not in exception_modules):
            filename = a.module
            module_path = module_f_path + filename + "/"
            branch_name = auto_update_branch(module_path, a.git, a.branch, a.tag, n_branch)
            res = 1
            if not (branch_name and len(branch_name) > 0):
                logging.info("自动创建分支失败 ++++" + a.pod)
                res = 0
            new_branch_model = YamlBranchModel(a.module, res)
            create_branch_result.append(new_branch_model)
        index += 1
        os.chdir(c_path)
    return create_branch_result


# 更新podfileModule文件
def update_module_files(yaml_path, local_yaml_path, branch_result, n_branch, modules_name):
    # 获取ymal 数据
    podfile_module_data = yaml_data(yaml_path)
    dependenceList = podfile_module_data["dependencies"]
    # 转换成模型数组
    conver_deplist = load_yaml(dependenceList)

    index = 0
    for a in conver_deplist:
        for mo_re in branch_result:
            if a.module and mo_re.module and a.module == mo_re.module and mo_re.result == 1:
                module_dict = {"module": mo_re.module, "pod": a.pod, "git": a.git, "configurations": a.configurations,
                               "inhibit_warnings": a.inhibit_warnings}
                dependenceList[index] = module_dict
        index += 1
    podfile_data = {"version": "1.0.0", "branch": n_branch, "dependencies": dependenceList}
    # podfile_module_data["dependencies"] = dependenceList
    update_yaml(yaml_path, podfile_data)

    shutil.copy(yaml_path, local_yaml_path)  # 复制文件
    local_dependenceList = []
    for mo_re in branch_result:
        if mo_re.result == 1:
            module_dict = {"module": mo_re.module, "pod": mo_re.module, "path": modules_name + "/" + mo_re.module}
            local_dependenceList.append(module_dict)
    local_module_data = {"version": "1.0.0", "dependencies": local_dependenceList}
    update_yaml(local_yaml_path, local_module_data)


# 创建分支的对象
# project_git 项目仓库地址
# project_branch 项目分支默认master
# project_tag 默认不指定
# project_path 默认~/Desktop/Project/{project_git中项目名}
# n_branch 新的分支，包括壳工程和组件，不指定默认为当前的年月日
class CreateBranch:
    git = ''
    branch = ""
    tag = ""
    path = ""
    n_branch = ""

    # 初始化
    def __init__(self, git, branch="master", tag="", path="", n_branch=""):
        _project_path = path
        if not (_project_path and len(_project_path) > 0):
            (file, ext) = os.path.splitext(git)
            (path, filename) = os.path.split(git)
            project_name = filename.replace(ext, "")
            _project_path = "~/Desktop/Project/" + project_name + "/"
        self.path = _project_path

        _n_branch = n_branch
        if not (_n_branch and len(_n_branch) > 0):
            today = datetime.date.today()
            for_today = today.strftime("%y%m%d")
            _n_branch = for_today
        self.n_branch = _n_branch

        self.git = git
        self.branch = branch
        self.tag = tag

    # 初始化项目仓库，自动拉取项目中的仓库
    def init_project(self, exception_module_list=[]):
        c_path = os.getcwd()
        fa_path = self.path
        modules_file_name = "modules"
        modules_path = fa_path + modules_file_name + "/"
        new_branch = self.n_branch
        # 新建或者清空工程目录
        # create_file(fa_path)
        # 拉取壳工程对应分支，tag，代码
        # 并新建一个开发分支
        # checkout_project(fa_path, self.git, self.branch, self.tag, self.n_branch)
        # 子目录，用来存放子模块仓库
        # create_file(modules_path)
        yamlPath = fa_path + 'PodfileModule.yaml'
        localyamlPath = fa_path + 'PodfileLocal.yaml'
        # 获取ymal 数据
        podfile_module_data = yaml_data(yamlPath)
        logging.info("读取yaml数据")
        # 获取依赖数据
        dependenceList = podfile_module_data["dependencies"]
        # 转换成模型数组
        conver_deplist = load_yaml(dependenceList)
        logging.info("转换成模型")
        branch_res = create_branch(conver_deplist, modules_path, new_branch, exception_module_list, c_path)
        if len(branch_res) > 0:
            update_module_files(yamlPath, localyamlPath, branch_res, new_branch, modules_file_name)
        if len(branch_res) == 0:
            logging.info("没有要自动创建分支的模块")
        else:
            succ_module = "分支创建成功的模块: \n"
            fail_module = "分支创建失败的模块: \n"
            for merg_Model in branch_res:
                if merg_Model.result == 1:
                    succ_module = succ_module + (merg_Model.module + "\n")
                else:
                    fail_module = fail_module + (merg_Model.module + "\n")
            logging.info(succ_module)
            logging.info(fail_module)

    # 只拉取子模块的代码，并修改依赖
    def update_modules(self, exeption_module_list=[]):
        c_path = os.getcwd()
        fa_path = self.path
        modules_file_name = "modules"
        modules_path = fa_path + modules_file_name + "/"
        n_branch = self.n_branch
        # 子目录，用来存放子模块仓库
        if not os.path.exists(modules_path):
            create_file(modules_path)
        yamlPath = fa_path + 'PodfileModule.yaml'
        localyamlPath = fa_path + 'PodfileLocal.yaml'
        # 获取ymal 数据
        podfile_module_data = yaml_data(yamlPath)
        logging.info("读取yaml数据")
        # 获取依赖数据
        dependenceList = podfile_module_data["dependencies"]
        branch = podfile_module_data["branch"]
        # 转换成模型数组
        conver_deplist = load_yaml(dependenceList)
        logging.info("转换成模型")
        branch_res = update_branch(conver_deplist, modules_path, n_branch, exeption_module_list, c_path, branch)
        if len(branch_res) > 0:
            update_module_files(yamlPath, localyamlPath, branch_res, n_branch, modules_file_name)
        if len(branch_res) == 0:
            logging.info("没有要自动创建分支的模块")
        else:
            succ_module = "分支创建成功的模块: \n"
            fail_module = "分支创建失败的模块: \n"
            for merg_Model in branch_res:
                if merg_Model.result == 1:
                    succ_module = succ_module + (merg_Model.module + "\n")
                else:
                    fail_module = fail_module + (merg_Model.module + "\n")
            logging.info(succ_module)
            logging.info(fail_module)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    cuPath = os.getcwd()
    fa_path = "../../Desktop/Project/yh-rme-srm-purchase-ios/"
    project_git = "http://gitlab.yonghui.cn/operation-pc-mid-p/yh-rme-srm-purchase-ios.git"
    # 分支的名字，如果没有指定将用年月日表示
    n_branch = "dev-20221101-8"
    cb = CreateBranch(git=project_git, path=fa_path)
    # cb.init_project()
    cb.update_modules()
    # os.chdir(fa_path)
    # os.system("pod install")
