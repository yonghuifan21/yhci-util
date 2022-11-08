
## [yhci-util](https://github.com/yonghuifan21/yhci-util): 一个多仓库管理插件

当项目存在多个组件依赖，我们可能有以下需求：

  需要在多个组件分别建立开发分支；同步多个组件的远程代码；提交多个组件的代码；合并开发分支到发布分支，并自动打tag
  
  以上需求分别基于每个组件进行操作，每项任务都将耗费大量的精力和时间。

  基于以上需求，开发了yhci-util插件，使用该插件可以很好的解决： 开发分支的创建，开发分支代码拉取，开发分支代码提交，开发分支合并到发布分支并打tag


### 环境

- Python >= 3.0

### 安装

如果你已经下载了最新的源码:

    python setup.py install

或者你可以通过pypi安装

    pip3 install yhcituil

这两个命令都将安装所需的包依赖项。

可以在以下位置获取分发包以进行手动安装

    http://pypi.python.org/pypi/yhciutil

如果你想从源代码克隆，你可以这样做:


```bash
git https://github.com/yonghuifan21/yhci-util.git
```

### 说明文档

#### 1. 通过 CreateBranch 创建一个对象，分别有以下四个参数

    git： 表示工程仓库地址
    branch： 表示工程基于哪个主分支新建开发分支，建议指定
    tag：表示工程基于哪个tag新建开发分支
    path：表示工程存放的地址
    n_branch： 开发分支的名字（主工程和组件的）

```
     __init__(self,git, branch="master", tag="", path="", n_branch="")
    
```
#### 2. 通过 init_project 初始化仓库，主要有以下参数 



    exception_module_list： 这里面的组件不新建开发分支，保持现有依赖
    clean_proj: 是否清空主项目地址，首次建议True，其他建议False

```
    def init_project(self, exception_module_list=[]):
```

    执行init_project内部过程： 
    1. 基于path新建文件夹用于存放主项目源码，如果path存在会清空
    2. 基于branch和tag拉取工程代码并放在path中
    3. 在path中新建modules目录，用于存放组件代码
    4. 根据PodfileModule.yaml中组件的依赖，新建n_branch分支，如果存在新分支就直接切换，并提交
    5. 更新PodfileModule.yaml中依赖为分支，更新PodfileLocal .yaml中依赖为路径依赖
  

#### 3. 通过 pull_modules 拉取开发分支最新代码

    exception_module_list： 这里面的组件不拉取最新代码

```
    def pull_modules(self, exception_module_list=[]):
```


    执行pull_modules内部过程： 
    3. 如果path中不存在modules，先在path中新建modules目录，用于存放组件代码
    4. 根据PodfileModule.yaml中组件的依赖，先判断是否存在目录， 如果本地没有组件对应目录，就新建目录，并走new_branch()逻辑；存在目录：在当前新分支，直接拉取代码；存在目录：本地不在新分支，异常提示拉取失败，需要手动切换到开发分支
    5. 更新PodfileModule.yaml中依赖为分支，更新PodfileLocal .yaml中依赖为路径依赖
    
    注意：init_project 在项目启动时只需要执行一次，如果第二次执行init_project时，会清空本地仓库地址，导致代码丢失
   
   #### 4. 通过 push_modules 拉取开发分支最新代码

    exception_module_list： 这里面的组件不拉取最新代码

```
    def push_modules(self, exception_module_list=[]):
```


    执行push_modules内部过程： 
    3. 如果path中不存在modules，先在path中新建modules目录，用于存放组件代码
    4. 根据PodfileModule.yaml中组件的依赖，先判断是否存在目录， 如果本地没有组件对应目录，提示异常；存在目录：在当前新分支，直接提交代码；存在目录：本地不在新分支，提示异常，需要手动切换到开发分支

 #### 5. 通过 merge_modules 拉取开发分支最新代码

    exception_module_list： 这里面的组件不拉取最新代码

````
    def merge_modules(self, exception_module_list=[]):
````


    执行merge_modules内部过程： 
    3. 如果path中不存在tagpath，先在path中新建tagpath目录，用于临时存放组件代码
    4. 根据PodfileModule.yaml中组件的依赖： clone开发分支代码；如果开发分支版本号大于master分支，那么新的版本号就是开发分支版本号，否则就自增1；更新版本号并提交代码；然后根据新版本号打tag，并提交到远端分支；更新PodfileModule.yaml中的依赖为tag，并清空PodfileLocal .yaml中的文件

    
### 怎么用

```
  # 新建一个python 文件
  # 引入依赖
  from branchmanager import CreateBranch
  # 方法调用
  if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    cuPath = os.getcwd()
    fa_path = "../../Desktop/Project/yh-rme-srm-purchase-ios/"
    project_git = "http://gitlab.yonghui.cn/operation-pc-mid-p/yh-rme-srm-purchase-ios.git"
    # 分支的名字，如果没有指定将用年月日表示
    n_branch = "221107"

    cb = CreateBranch(git=project_git, path=fa_path, n_branch=n_branch)
    # 初始化项目
    # cb.init_project(clean_proj=False)
    # 拉取远端代码
    # cb.pull_modules()
    # 提交本地代码
    # cb.push_modules()
    # 开发完成，合并开发分支打tag
    cb.merge_modules()
   

```
