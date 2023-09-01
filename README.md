<div align="center">

<img src="assets/icon.png" alt="icon" width="20%">

<h1 align="center">E站(nku eamis)助手</h1>


</div>

## Usage

```python
from eamis import eamis
eamis.login("YOUR_STU_ID", "YOUR_PASSWORD")
eamis.cookie_eamis # use this for course electing

```

## To-Do

- [X] 绕过SSO滑动验证码(迫真)登录E站
- [X] 获取其他cookies参数：`semester.id`
- [X] 选课相关
  - [X] 选课列表获取
  - [X] 课程列表获取
  - [X] 上限已选人数获取
  - [X] 进行一个课的选
- [ ] CLI
- [ ] 计划运行器
- [ ] Json-based Triggers & Flows
