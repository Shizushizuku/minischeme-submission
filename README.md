# mini-Scheme 解释器

用 Python 3.9+ 实现的 mini-Scheme 解释器，入口是 `src/main.py`，只依赖 Python 标准库。

## 运行

在本文件夹运行：

```sh
python3 src/main.py example/01_arithmetic.scm
python3 src/main.py file1.scm file2.scm
python3 src/main.py < file.scm
```

Windows 上可将 `python3` 换为 `py -3`，或使用本机 Python 可执行文件的路径。多个文件按顺序执行，共享全局环境。每个有值的顶层表达式输出一行；`display` 和 `newline` 自行控制输出。

## 测试

```sh
python3 -m unittest discover -s tests -v
```

`tests/` 包含语言规则和命令行行为的回归测试；`example/` 包含六个示例程序。开发时原项目附带的评分器 12 组验收全部通过，以上 24 项回归测试也全部通过。

## 结构

- `src/lexer.py`、`src/parser.py`：读取程序文本与表达式。
- `src/values.py`、`src/environment.py`：点对、过程和词法环境。
- `src/evaluator.py`、`src/primitives.py`：特殊形式、函数调用和内置过程。
- `src/printer.py`、`src/main.py`：结果格式化及命令行入口。
