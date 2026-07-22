# 贡献指南

感谢您对 Student Presentation Suite 的兴趣！

## 开发设置

```bash
# 克隆仓库
git clone https://github.com/YFan945/Personal-Student.git
cd Personal-Student

# Python 依赖
pip install -r plugins/student-presentation-suite/requirements.txt
pip install -r plugins/student-presentation-suite/requirements-claude-pptx.txt

# Node.js 依赖
npm --prefix plugins/student-presentation-suite ci
```

## 运行测试

```bash
cd plugins/student-presentation-suite
PYTHONPATH=. python -m unittest discover -s tests
```

## 代码质量

- Python 代码使用 Ruff（`ruff check .`）
- JavaScript 代码使用 ESLint + Prettier（`npx eslint scripts/*.js`）
- 提交前运行测试确保无回归

## 工作流

1. 从 `claude-code` 创建功能分支
2. 实施修改并添加测试
3. 运行全部测试确保通过
4. 提交 PR 到 `claude-code` 分支

## 版本发布

版本号遵循 semver，使用 `bump_version.py` 统一更新。
