# DeePEST Gaussian External

基于 DeePEST-OS 公开权重封装的 Gaussian 16 `External` 接口，面向 PBS 批量任务。

## 目录

- `g16-deepest/`: `g16-mlips-deepest` 包源码
- `upstream/DeePEST-OS/`: 上游 DeePEST-OS 参考文件与已下载模型
- `deepest_g16.yaml`: 独立 conda 环境
- `setup_deepest_g16.sh`: 环境创建与本地安装脚本
- `deepest 脚本/`: Gaussian 输入生成与 PBS 提交脚本
- `mace&orb 脚本/`: 原有参考脚本

## 核心模型

- 默认主模型：`upstream/DeePEST-OS/models/MACE_deltaL/MACE_deltaL.model`
- 备选 CHON 模型：`upstream/DeePEST-OS/models/DeePEST-OS-T1x/DeePEST-OS-T1x.model`

## 基本用法

Linux 集群上建议：

```bash
bash setup_deepest_g16.sh
conda activate deepest_g16
bash "deepest 脚本/generate_all_inputs.sh"
qsub -v NODE_ID=1,INPUT_ROOT=DEEPEST_Inputs_All "deepest 脚本/submit_all_models.pbs"
```

## 说明

- DeePEST 总势能面定义为 `GFN2-xTB + delta-MACE`
- 该接口继续沿用 Gaussian `Freq -> Opt(ReadFC,NoMicro) -> Freq` 工作流
- 真实联调仍需在 Linux + Gaussian 16 + PBS 环境中完成
