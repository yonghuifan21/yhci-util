# author: "jack-fan"
# date:2022/11/07 10:10

import os
import shutil
import ruamel.yaml
import datetime
from git import Repo
import logging
import re
from urllib.parse import urlparse


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
        """
        :param module:
        :param pod:
        :param version:
        :param git:
        :param branch:
        :param tag:
        :param path:
        :param newtag:
        :param configurations:
        :param inhibit_warnings:
        """
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
    tag = ''

    def __init__(self, module, res, tag=''):
        """
        :param module: 模块名字
        :param res: 结果 0 表示失败 1 表示成功
        """
        self.module = module
        self.result = res
        self.tag = tag


# 读取yaml文件数据
def yaml_data(yaml_path):
    """
    :param yaml_path: ymal路径
    :return: 返回yaml数据
    """
    with open(yaml_path, 'r') as y:
        yaml = ruamel.yaml.YAML()
        temp_yaml = yaml.load(y.read())
        return temp_yaml


# 写入文件
def update_yaml(yaml_path, data):
    """
    :param yaml_path: yaml路径
    :param data: yaml数据
    :return: 无返回值
    """
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml = ruamel.yaml.YAML()
        yaml.dump(data, f)


# 加载yml文件
def load_yaml(data):
    """
    :param data: 读取yaml数据
    :return: 返回转换之后的模型
    """
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
    """
    :param path_data: 文件路径
    :return: 无返回值
    """
    # os.listdir(path_data)#返回一个列表，里面是当前目录下面的所有东西的相对路径
    shutil.rmtree(path_data)


# 获取所有的分支
def get_branches(project_dir):
    """
    :param project_dir: 文件路径
    :return: 返回分支列表
    """
    repo = Repo(path=project_dir, search_parent_directories=True)
    branch_list = repo.git.branch("-r")
    return branch_list


# 获取podspec对应的版本号
def get_version_for(pod_spec_path):
    """
    获取tag版本号
    :param pod_spec_path: podspec路径
    :param new_tag: 新的tag名字
    :return:
    """
    with open(pod_spec_path, 'r', encoding="utf-8") as f:
        for line in f:
            if "s.version" in line and "s.source" not in line:
                # 获取版本号
                cur_tag = tag_with_version(line)
                return cur_tag
        f.close()
        return ""


# 重写podspec里对应的版本
def update_versionfor_podspec(pod_spec_path, new_tag):
    """
    重写podspec里对应的版本
    :param pod_spec_path: podspec路径
    :param new_tag: 新tag
    :return:
    """
    file_data = ""
    with open(pod_spec_path, 'r', encoding="utf-8") as f:
        for line in f:
            if "s.version" in line and "s.source" not in line:
                cur_tag = tag_with_version(line)
                line = line.replace(cur_tag, new_tag)
                print("修改tag " + cur_tag + " => " + new_tag)
            file_data += line
    with open(pod_spec_path, 'w', encoding="utf-8") as f:
        f.write(file_data)
        f.close()


# 获取字符串中的版本信息
def tag_with_version(version):
    """
    获取字符串中的版本信息
    :param version: 版本号
    :return:
    """
    p = re.compile(r'\d+\.(?:\d+\.)*\d+')
    vers = p.findall(version)
    ver = vers[0]
    return ver


# 根据tag自增生成新的tag
def incre_tag(tag):
    """
    tag最后一位自增
    :param tag: 原tag
    :return: 返回最后一位自增1后的tag
    """
    tags = tag.split(".")
    tag_len = len(tags)
    if tag_len > 1:
        endtag = tags[tag_len - 1]
        end_tag_num = int(endtag) + 1
        endtag = str(end_tag_num)
        tags[tag_len - 1] = endtag

    new_tag = ".".join(tags)
    return new_tag

def get_filename(url_str):
    url = urlparse(url_str)
    i = len(url.path) - 1
    while i > 0:
        if url.path[i] == '/':
            break
        i = i - 1
    folder_name = url.path[i + 1:len(url.path)]
    if not folder_name.strip():
        return False
    if ".git" in folder_name:
        folder_name = folder_name.replace(".git", "")
    return folder_name

# 判断两个版本的大小，去除小数点，变为整数数组，依次比较大小1
# 2.2.3 = [2, 2, 3]
# 2.2.10 = [2, 2, 10]  2.2.10 > 2.2.3
# 相等返回0， v1 > v2 返回 1 v1 < v2 返回 -1
def compare_version(v1, v2):
    """
    比较两个tag， 判断两个版本的大小，去除小数点，变为整数数组，依次比较大小1
    :param v1: v1 tag入参
    :param v2:  v2 tag 入参
    :return: 相等返回0， v1 > v2 返回 1 v1 < v2 返回 -1
    """
    v1_list = v1.split(".")
    v2_list = v2.split(".")
    max_len = max(len(v1_list), len(v2_list))
    idx = 0
    while idx < max_len:
        c_v1 = 0
        c_v2 = 0
        if len(v1_list) > idx:
            c_v1 = int(v1_list[idx])
        if len(v2_list) > idx:
            c_v2 = int(v2_list[idx])
        if c_v2 > c_v1:
            return -1
        else:
            return 1
        idx += 1
    return 0


# 基于master 和 f_tag，创建一个新的分支new_branch，如果存在仓库则先清空仓库，再拉取分支
# 1. 清空当前工作目录
# 2. 拉取代码
# 3. 新建分支
# 4. 推送分支
def auto_create_branch(filepath, git, f_branch, f_tag, n_branch):
    """
    :param filepath: 文件路径
    :param git: git地址
    :param f_branch: 基于哪个分支切一个新的开发分支
    :param f_tag: 基于哪个tag切开发分支
    :param n_branch: 新分支名
    :return: 成功返回新分支名，失败返回空字符串
    """
    # 创建分支
    create_file(filepath)
    return new_branch(filepath, git, f_branch, f_tag, n_branch)


# 新建分支
def new_branch(filepath, git, f_branch, f_tag, n_branch):
    """
    f_branch 和 f_tag，创建一个新的分支n_branch
    2. 拉取代码
    3. 判断是否存在新分支，有新分支直接切到新分支
    3. 新建分支
    4. 切换到新分支
    4. 推送分支
    :param filepath: 路径
    :param git: git地址
    :param f_branch: 基于哪个分支切一个新的开发分支
    :param f_tag:  基于哪个tag切开发分支
    :param n_branch: 新分支名
    :return: 成功返回新分支名，失败返回空字符串
    """
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
    git_push_command = "git push -u origin " + n_branch
    create_status = 0
    create_status += os.system(git_clone_command)
    logging.info("执行 " + git_clone_command)
    # master分支下的版本号
    branchs = get_branches(filepath)
    os.chdir(filepath)
    if n_branch in branchs:
        os.system(git_checkout_command)
        logging.info(n_branch + "分支已存在")
        return n_branch
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
    """
    基于n_branch，将开发分支切到n_branch中
    1. 如果本地没有组件对应目录，就新建目录，并走new_branch()逻辑
    2. 存在目录：在当前新分支，直接拉取代码，
    3. 存在目录：本地不在新分支，异常提示拉取失败，手动切换到开发分支
    :param filepath: 路径
    :param git: git地址
    :param f_branch: 基于哪个分支切一个新的开发分支
    :param f_tag:  基于哪个tag切开发分支
    :param n_branch: 新分支名
    :return: 成功返回新分支名，失败返回空字符串
    """
    _branch = f_branch
    if not (f_branch and len(f_branch) > 0):
        _branch = "master"
    # 创建分支
    if os.path.exists(filepath):
        # 存在目录，判断当前处于哪个分支下
        try:
            repo = Repo(path=filepath, search_parent_directories=True)
        except:
            br = new_branch(filepath, git, _branch, f_tag, n_branch)
            return br
        fapath = os.getcwd()
        c_branch = repo.active_branch.name
        (file, ext) = os.path.splitext(git)
        (path, filename) = os.path.split(git)
        module_name = filename.replace(ext, "")
        # 判断当前分支是不是是指定的开发分支
        if c_branch == f_branch:
            # git add 代码
            git_add_command = "git add -A"
            # git commit 代码
            git_commit_command = "git commit -m \'自动提交\'"
            # git pull branch 代码
            git_pull_command = "git pull origin " + c_branch
            os.chdir(filepath)
            os.system(git_add_command)
            logging.info("执行 " + git_add_command)
            os.system(git_commit_command)
            logging.info("执行 " + git_commit_command)
            pul_status = os.system(git_pull_command)
            if not pul_status == 0:
                os.chdir(fapath)
                logging.error("模块：" + module_name + " 分支: " + f_branch + " 代码拉取失败")
                return ""
            os.chdir(fapath)
        else:
            logging.error("模块：" + module_name + " 分支: " + c_branch + " 不在开发分支拉不了最新代码")
            return ""

        return n_branch
    else:
        create_file(filepath)
        br = new_branch(filepath, git, _branch, f_tag, n_branch)
        return br


# 基于master 和 f_tag，创建一个新的分支new_branch, 如果文件目录存在，则判断当前是否在dui'y
# 1. 清空当前工作目录
# 2. 拉取代码
# 3. 新建分支
# 4. 推送分支
# 5. 提交代码
def auto_push_branch(filepath, git, f_branch, f_tag, n_branch):
    """
    将代码提交到n_branch
    1. 如果本地没有组件对应目录，异常提示错误
    2. 存在目录：在当前新分支，直接提交代码，
    3. 存在目录：本地不在新分支，异常提示错误
    :param filepath: 路径
    :param git: git地址
    :param f_branch: 基于哪个分支切一个新的开发分支
    :param f_tag:  基于哪个tag切开发分支
    :param n_branch: 新分支名
    :return: 成功返回新分支名，失败返回空字符串
    """
    (file, ext) = os.path.splitext(git)
    (path, filename) = os.path.split(git)
    module_name = filename.replace(ext, "")
    _branch = f_branch
    if not (f_branch and len(f_branch) > 0):
        _branch = "master"
    # 创建分支
    print(os.getcwd())
    fapath = os.getcwd()
    if os.path.exists(filepath):
        # 存在目录，判断当前处于哪个分支下
        try:
            repo = Repo(path=filepath, search_parent_directories=True)
        except:
            br = new_branch(filepath, git, _branch, f_tag, n_branch)
            return br
        c_branch = repo.active_branch.name
        # 判断当前分支是不是是指定的开发分支
        if c_branch == f_branch:
            # git add 代码
            git_add_command = "git add -A"
            # git commit 代码
            git_commit_command = "git commit -m \'自动提交\'"
            # git pull branch 代码
            git_pull_command = "git pull origin " + c_branch
            # git push
            git_push_command = "git push origin master"
            os.chdir(filepath)
            os.system(git_add_command)
            logging.info("执行 " + git_add_command)
            os.system(git_commit_command)
            logging.info("执行 " + git_commit_command)
            pul_status = os.system(git_pull_command)
            if not pul_status == 0:
                os.chdir(fapath)
                logging.error("模块：" + module_name + " 分支: " + f_branch + " 提交失败")
                return ""
            pul_status += os.system(git_push_command)
            if not pul_status == 0:
                os.chdir(fapath)
                logging.error("模块：" + module_name + " 分支: " + f_branch + " 提交失败")
                return ""

            os.chdir(fapath)
            return n_branch
        else:
            logging.error("模块：" + module_name + " 分支: " + c_branch + " 不在开发分支提交不了")
            return ""

        return n_branch
    else:
        logging.error("模块：" + module_name + "分支: " + f_branch + " 本地没有组件的工作目录，没法自动提交代码")
        return ""


# 自动打tag 自动合并失败时返回空字符串
# 1. 清空当前工作目录
# 2. 拉取代码
# 3. 修改s.version
# 4. 提交代码
# 5. 拉取工作分支
# 5. 推送代码
def auto_merge_path(filepath, git, pod, branch, new_tag):
    """
    自动合并branch到master中，并提交tag
    :param filepath: 文件路径
    :param git: git地址
    :param pod: pod模块
    :param branch: 分支
    :param new_tag: 新tag
    :return:
    """
    create_file(filepath)

    # return
    # 进入模块
    # clone 代码
    git_clone_command = "git clone -b master" + " " + git + " " + filepath
    # git add 代码
    git_add_command = "git add -A"
    # git commit 代码
    git_commit_command = "git commit -m \'修改podspec文件\'"
    # git pull branch 代码
    git_pull_command = "git pull origin " + branch
    # git push
    git_push_command = "git push origin master"
    # 用newTag来修改podspec中version
    os.system(git_clone_command)
    print("执行 " + git_clone_command)
    # master分支下的版本号
    os.chdir(filepath)
    cur_tag = get_version_for(pod + ".podspec")
    os.system("pwd")
    os.system("ls")
    os.system(git_add_command)
    print("执行 " + git_add_command)
    os.system(git_commit_command)
    print("执行 " + git_commit_command)
    pul_status = os.system(git_pull_command)
    print("执行 " + git_pull_command)
    if not pul_status == 0:
        print("代码冲突了")
        return ""
    dev_branch_tag = get_version_for(pod + ".podspec")
    new_tag_p = dev_branch_tag
    if dev_branch_tag == cur_tag:
        # 版本号一样就最后一位自增
        new_tag_p = incre_tag(cur_tag)
    else:
        # 版本号不一样，就比较如果开发分支比较大就用开发分支，否则还是自增
        res = compare_version(dev_branch_tag, cur_tag)
        if res == -1:
            new_tag_p = incre_tag(cur_tag)

    update_versionfor_podspec(pod + ".podspec", new_tag_p)
    os.system(git_add_command)
    print("执行 " + git_add_command)
    os.system(git_commit_command)
    print("执行 " + git_commit_command)
    print("代码已经提交到master")

    os.system(git_push_command)
    print("执行 " + git_push_command)
    return new_tag_p


# 基于master 和 f_tag，创建一个新的分支new_branch
# 1. 清空当前工作目录
# 2. 拉取代码
# 3. 新建分支
# 4. 推送分支
def auto_delete_branch(filepath, git, f_branch, f_tag, n_branch):
    """
    删除n_branch
    :param filepath: 文件路径
    :param git: 仓库地址
    :param f_branch: 原分支
    :param f_tag: 原tag
    :param n_branch: 要删除的分支
    :return:
    """
    # 创建分支
    create_file(filepath)
    f_branch = f_branch
    if not (f_branch and len(f_branch) > 0):
        f_branch = "master"
    # clone 代码
    git_clone_command = "git clone -b " + f_branch + " " + git + " " + filepath
    # 删除n_branch 分支
    git_push_command = "git push origin --delete " + n_branch
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
    """
    基于c_branch和c_tag，新建一个分支n_branch
    :param filepath: 主项目本地目录
    :param git: git地址
    :param c_branch: 基于哪个分支切开发分支
    :param c_tag: 基于哪个tag切开发分支
    :param n_branch: 新分支名
    :return:
    """
    # return
    # 进入模块
    # clone 代码
    c_branch = c_branch
    if not (c_branch and len(c_branch) > 0):
        c_branch = "master"

    git_clone_command = "git clone -b " + c_branch + " " + git + " " + filepath
    # remote add origin
    git_remote_origin = "git remote add  origin " + git
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
    clone_status += os.system(git_remote_origin)
    logging.info(clone_status)
    os.system(git_create_branch)
    os.system(git_checkout_command)
    os.system(git_push_branch)
    logging.info("壳工程目录：" + filepath)


# 清空或者创建一个新的目录
def create_file(path):
    """
    情况或者创建一个目录
    :param path: 目录
    :return:
    """
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        del_file(path)
        os.makedirs(path)


# 基于podfileModule来给每个组件创建一个分支
def create_branch(module_list, module_f_path, n_branch, exception_modules, c_path):
    """
    基于列表，拉取对应代码，并创建一个开发分支
    :param module_list: 模块列表
    :param module_f_path: 路径
    :param n_branch: 新分支
    :param exception_modules: 这个模块排除在外，不新建n_branch分支
    :param c_path: 当前的工作目录
    :return:
    """
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
    """
    基于列表，拉取对应对应开发分支代码，如果没有对应分支就创建一个n_branch分支
    :param module_list: 模块列表
    :param module_f_path: 路径
    :param n_branch: 新分支
    :param exception_modules:  这些模块排除在外，不拉取n_branch对应代码
    :param c_path: 当前运行分支
    :param f_branch: 配置的全局统一分支，每个模块可以单独配置分支
    :return: 返回操作成功的分支
    """

    index = 0
    create_branch_result = []
    for a in module_list:
        if not (a.branch and len(a.branch) > 0) and not (a.tag and len(a.tag) > 0):
            a.branch = f_branch
        if ((a.branch and len(a.branch) > 0) or (a.tag and len(a.tag) > 0)) and (
                a.module not in exception_modules):
            filename = a.module
            module_path = module_f_path + filename + "/"
            branch_name = auto_update_branch(module_path, a.git, a.branch, a.tag, n_branch)
            res = 1
            if not (branch_name and len(branch_name) > 0):
                logging.info("自动提交代码失败 ++++" + a.pod)
                res = 0
            new_branch_model = YamlBranchModel(a.module, res)
            create_branch_result.append(new_branch_model)
        index += 1
        os.chdir(c_path)
    return create_branch_result


# 基于podfileModule，提交模块开发分支代码
def push_branch(module_list, module_f_path, n_branch, exception_modules, c_path, f_branch):
    """
    基于列表，提交对应开发分支代码
    :param module_list: 模块列表
    :param module_f_path: 路径
    :param n_branch: 新分支
    :param exception_modules:  这些模块排除在外，不提交n_branch代码
    :param c_path: 当前运行分支
    :param f_branch: 配置的全局统一分支，每个模块可以单独配置分支
    :return: 返回操作成功的分支
    """

    index = 0
    create_branch_result = []
    for a in module_list:
        if not (a.branch and len(a.branch) > 0) and not (a.tag and len(a.tag) > 0):
            a.branch = f_branch
        if ((a.branch and len(a.branch) > 0) or (a.tag and len(a.tag) > 0)) and (
                a.module not in exception_modules):
            filename = a.module
            module_path = module_f_path + filename + "/"
            branch_name = auto_push_branch(module_path, a.git, a.branch, a.tag, n_branch)
            res = 1
            if not (branch_name and len(branch_name) > 0):
                logging.info("自动提交分支失败 ++++" + a.pod)
                res = 0
            new_branch_model = YamlBranchModel(a.module, res)
            create_branch_result.append(new_branch_model)
        index += 1
        os.chdir(c_path)
    return create_branch_result


# 基于podfileModule，提交模块开发分支代码
def merge_branch(module_list, tag_path, exception_modules, c_path, f_branch):
    """
    基于模块列表，合并对应开发分支代码到master并打新的tag
    :param module_list: 模块列表
    :param exception_modules:  这些模块排除在外，不提交n_branch代码
    :param c_path: 当前运行分支
    :param f_branch: 配置的全局统一分支，每个模块可以单独配置分支
    :return: 返回操作成功的分支
    """

    index = 0
    merge_result = []
    for a in module_list:
        if not (a.branch and len(a.branch) > 0) and not (a.tag and len(a.tag) > 0):
            a.branch = f_branch
        if (a.branch and len(a.branch) > 0) and (
                a.module not in exception_modules):
            filename = get_filename(a.git)
            module_path = tag_path + filename + "/"
            new_tag = a.new_tag
            create_tag = auto_merge_path(module_path, a.git, a.pod, a.branch, a.new_tag)
            result = 0
            if not (create_tag and len(create_tag) > 0):
                print("自动打包失败 ++++" + a.pod)
            else:
                result = 1
                a.new_tag = create_tag
            merge_model = YamlBranchModel(a.module, result, create_tag)
            merge_result.append(merge_model)
        index += 1
        os.chdir(c_path)
    return merge_result


# 更新podfileModule文件
def update_module_files(yaml_path, local_yaml_path, branch_result, n_branch, modules_name):
    """
    更新ymal文件，修改本地依赖和分支依赖
    :param yaml_path: PodfileModule路径
    :param local_yaml_path: PodfileLocal路径
    :param branch_result: 操作成功的模块列表
    :param n_branch: 新分支名
    :param modules_name: 模块仓库的父路径默认为modules
    :return:
    """
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
    update_yaml(yaml_path, podfile_data)

    shutil.copy(yaml_path, local_yaml_path)  # 复制文件
    local_dependenceList = []
    for mo_re in branch_result:
        if mo_re.result == 1:
            module_dict = {"module": mo_re.module, "pod": mo_re.module, "path": modules_name + "/" + mo_re.module}
            local_dependenceList.append(module_dict)
    local_module_data = {"version": "1.0.0", "dependencies": local_dependenceList}
    update_yaml(local_yaml_path, local_module_data)


# 更新podfileModule文件
def merge_for_module_files(yaml_path, branch_result, n_branch):
    """
    更新ymal文件，修改本地依赖和分支依赖
    :param yaml_path: PodfileModule路径
    :param local_yaml_path: PodfileLocal路径
    :param branch_result: 操作成功的模块列表
    :param n_branch: 新分支名
    :param modules_name: 模块仓库的父路径默认为modules
    :return:
    """
    # 获取ymal 数据
    podfile_module_data = yaml_data(yaml_path)
    dependenceList = podfile_module_data["dependencies"]
    # 转换成模型数组
    conver_deplist = load_yaml(dependenceList)

    index = 0
    for a in conver_deplist:
        for mo_re in branch_result:
            if a.module and mo_re.module and a.module == mo_re.module and mo_re.result == 1:
                module_dict = {"module": mo_re.module, "pod": a.pod, "git": a.git, "tag": mo_re.tag, "configurations": a.configurations,
                               "inhibit_warnings": a.inhibit_warnings}
                dependenceList[index] = module_dict
        index += 1
    podfile_data = {"version": "1.0.0", "branch": n_branch, "dependencies": dependenceList}
    update_yaml(yaml_path, podfile_data)


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
        """
        基于项目git地址拉取代码，并通过读取PodfileModule中的组件依赖，来新建开发分支n_branch，或者更新本地仓库
        :param git: 工程git地址
        :param branch: 基于哪个分支新建开发分支， 默认master
        :param tag: 基于哪个tag来新建开发分支， 默认不指定
        :param path: 项目的路径，默认~/Desktop/Project/ + 项目名
        :param n_branch: 新分支名， 默认当前年月日
        """
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
    def init_project(self, exception_module_list=[], clean_proj=True):
        """
        基于初始化的配置信息，初始化开发分支； 创建工程目录，创建每个模块的工作目录，创建开发分支，创建工作目录
        :param exception_module_list: 这些模块不做修改，不创建分支，保持原来的依赖。
        :param init_proj: 是否要清空项目仓库，默认清空
        :param clean_proj: 是否清空壳工程仓库
        :return:
        """
        c_path = os.getcwd()
        fa_path = self.path
        modules_file_name = "modules"
        modules_path = fa_path + modules_file_name + "/"
        new_branch = self.n_branch
        # 新建或者清空工程目录
        if not (os.path.exists(fa_path) and not clean_proj):
            create_file(fa_path)

        # 拉取壳工程对应分支，tag，代码
        # 并新建一个开发分支
        if not (os.path.exists(fa_path) and not clean_proj):
            checkout_project(fa_path, self.git, self.branch, self.tag, self.n_branch)
        # 子目录，用来存放子模块仓库
        create_file(modules_path)
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
    def pull_modules(self, exeption_module_list=[]):
        """
        基于初始化的配置信息，更新本地的依赖，并拉去对应开发分支的代码
        :param exeption_module_list: 这些模块不做修改，拉取代码。
        :return:
        """
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
            logging.info("没有要更新分支的模块")
        else:
            succ_module = "分支更新成功的模块: \n"
            fail_module = "分支更新失败的模块: \n"
            for merg_Model in branch_res:
                if merg_Model.result == 1:
                    succ_module = succ_module + (merg_Model.module + "\n")
                else:
                    fail_module = fail_module + (merg_Model.module + "\n")
            logging.info(succ_module)
            logging.info(fail_module)

    # 自动提交子模块的代码
    def push_modules(self, exeption_module_list=[]):
        """
        基于podfileModules的配置信息，提交本地开发分支代码
        :param exeption_module_list: 这些模块不需要修改，不能提交代码
        :return:
        """
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
        branch_res = push_branch(conver_deplist, modules_path, n_branch, exeption_module_list, c_path, branch)
        # if len(branch_res) > 0:
        #     update_module_files(yamlPath, localyamlPath, branch_res, n_branch, modules_file_name)
        if len(branch_res) == 0:
            logging.info("没有要提交代码的模块")
        else:
            succ_module = "代码提交成功的模块: \n"
            fail_module = "代码提交失败的模块: \n"
            for merg_Model in branch_res:
                if merg_Model.result == 1:
                    succ_module = succ_module + (merg_Model.module + "\n")
                else:
                    fail_module = fail_module + (merg_Model.module + "\n")
            logging.info(succ_module)
            logging.info(fail_module)

    # 自动提交子模块的代码
    def merge_modules(self, exeption_module_list=[]):
        """
        基于podfileModules的配置信息，merge开发分支到master，获取开发分支的版本号，如果版本号大于master分支，新的tag就为开发分支版本号，如果版本号相等，那那么就末尾自增1，自动打tag
        :param exeption_module_list: 这些模块不需要修改，不能提交代码
        :return:
        """
        c_path = os.getcwd()
        fa_path = self.path
        modules_file_name = "tagpath"
        modules_path = fa_path + modules_file_name + "/"
        # 子目录，用来存放子模块仓库
        if not os.path.exists(modules_path):
            create_file(modules_path)
        yamlPath = fa_path + 'PodfileModule.yaml'
        # 获取yaml 数据
        podfile_module_data = yaml_data(yamlPath)
        logging.info("读取yaml数据")
        # 获取依赖数据
        dependenceList = podfile_module_data["dependencies"]
        branch = podfile_module_data["branch"]
        # 转换成模型数组
        conver_deplist = load_yaml(dependenceList)
        logging.info("转换成模型")
        branch_res = merge_branch(conver_deplist, modules_path, exeption_module_list, c_path, branch)
        if len(branch_res) > 0:
            merge_for_module_files(yamlPath, branch_res, branch)
        if len(branch_res) == 0:
            logging.info("没有要提交代码的模块")
        else:
            succ_module = "代码提交成功的模块: \n"
            fail_module = "代码提交失败的模块: \n"
            for merg_Model in branch_res:
                if merg_Model.result == 1:
                    succ_module = succ_module + (merg_Model.module + "\n")
                else:
                    fail_module = fail_module + (merg_Model.module + "\n")
            logging.info(succ_module)
            logging.info(fail_module)
        if os.path.exists(modules_path):
            del_file(modules_path)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    cuPath = os.getcwd()
    fa_path = "../../Desktop/Project/yh-rme-srm-purchase-ios/"
    n_branch = "221107"
    project_git = "http://gitlab.yonghui.cn/operation-pc-mid-p/yh-rme-srm-purchase-ios.git"
    # 分支的名字，如果没有指定将用年月日表示
    n_branch = "dev-20221101-8"
    cb = CreateBranch(git=project_git, path=fa_path)
    # cb.init_project()
    # cb.pull_modules()
    cb.push_modules()
    # os.chdir(fa_path)
    # os.system("pod install")
