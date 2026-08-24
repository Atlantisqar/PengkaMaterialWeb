# TX.NET Type-C 串口与拨码切换改版

本目录基于原始 `TX.NET` 网表重建接口关系，并新增 USB Type-C 串口。原电路的 `DATA`、`TXEN`、`VMOTOR_10V` 和 3.3 V 稳压部分保持不变。

## 设计结论

- 板内串口电平：3.3 V（原板 `VCC` 由 TLV76133 产生）。
- USB-UART：`CP2102N-GQFN20`，使用板上 `VCC` 自供电。
- Type-C：仅用于 USB 2.0 串口通信，不从 `VBUS` 给整板供电。
- 接口选择：`SW1` 是一位 SPST 拨码开关，控制 `TMUX1574` 的 `SEL`，同时切换 TX/RX 两路。
- 默认状态：SW1 断开时选择杜邦排针；SW1 闭合时选择 Type-C。
- USB 防护：D+/D- 使用 `USBLC6-2SC6`；CC1、CC2 各用 5.1 kΩ 下拉。
- 防反灌：TMUX1574 带 powered-off protection；Type-C 桥与原板共用 3.3 V 电源域。

## 串口切换关系

| SW1 | SEL | TXD_CORE 连接到 | RXD_CORE 连接到 | 模式 |
|---|---:|---|---|---|
| OFF | 0 | H1-1（杜邦 TX） | H1-2（杜邦 RX） | 杜邦线 |
| ON | 1 | CP2102N RXD | CP2102N TXD | Type-C |

注意：UART 必须交叉连接。板内 `TXD_CORE` 接 USB-UART 的 `RXD`，板内 `RXD_CORE` 接 USB-UART 的 `TXD`。

## 关键连接

### TMUX1574（U5，TSSOP-16）

- `D1`(4) = `TXD_CORE`
- `S1A`(2) = `DUPONT_TX`
- `S1B`(3) = `USB_UART_RX`
- `D2`(7) = `RXD_CORE`
- `S2A`(5) = `DUPONT_RX`
- `S2B`(6) = `USB_UART_TX`
- `SEL`(1) = `UART_SEL`；R10 100 kΩ 下拉，SW1 闭合时接 VCC
- `/EN`(15) = GND
- `VDD`(16) = VCC，C14 100 nF 就近去耦
- 第 3、4 通道悬空不用

### CP2102N-GQFN20（U4）

- `D+`(4)、`D-`(5) 经 U6 ESD 保护接 Type-C
- `VDD`(6)、`VREGIN`(7) 接板上 VCC；每个电源脚旁各放 4.7 µF + 100 nF
- `VBUS`(8) 通过 22.1 kΩ / 47.5 kΩ 分压检测 Type-C VBUS
- `/RST`(9) 通过 1 kΩ 上拉到 VCC
- `RXD`(17) = `USB_UART_RX`
- `TXD`(18) = `USB_UART_TX`
- GND 脚与裸露焊盘接地
- 其余握手、GPIO 和状态脚未使用，保持 NC

### USB Type-C（J1）

- A6/B6 并联为 D+
- A7/B7 并联为 D-
- A5(CC1)、B5(CC2) 分别用 5.1 kΩ 接地，不可共用一个电阻
- A4/A9/B4/B9 并联为 VBUS，仅用于 U4 的 VBUS 检测
- 所有 GND 与屏蔽焊脚接板上 GND
- SBU1、SBU2 悬空

## PCB 布局要点

1. J1、U6、U4 按“连接器 → ESD → CP2102N”的顺序紧凑放置。
2. D+/D- 按 90 Ω 差分阻抗布线，等长、少过孔、不中断参考地平面；不要在差分线上留测试点长支路。
3. CC 电阻靠近 Type-C 连接器；U4/U5 去耦电容靠近对应电源脚。
4. USB 屏蔽外壳优先在连接器附近多过孔接地。
5. 丝印明确标注 `SW1 OFF=DUPONT / ON=TYPE-C`；切换前停止串口收发。

## 文件

- `TX_TypeC_UART.NET`：加入 Type-C、USB-UART 和切换电路后的完整网表。
- `TX_TypeC_UART_BOM.csv`：新增器件 BOM。
- `TX_TypeC_UART_schematic.svg`：新增电路的可缩放原理图。
- `SOURCE_TX.NET`：原始输入网表副本。

## 设计边界

原始输入只有网表，没有原理图坐标、PCB、连接器具体料号或机械尺寸。因此本版给出可制造的电气方案和完整连接关系，但 Type-C 连接器封装必须在选定实物料号后核对焊盘编号与外壳尺寸；投板前还应在目标 EDA 中执行 ERC/DRC，并按实际板框复核 USB 差分阻抗。

## 主要器件资料

- Silicon Labs：[CP2102N datasheet](https://www.silabs.com/documents/public/data-sheets/cp2102n-datasheet.pdf)
- Texas Instruments：[TMUX1574 datasheet](https://www.ti.com/lit/ds/symlink/tmux1574.pdf)
- STMicroelectronics：[USBLC6-2 datasheet](https://www.st.com/resource/en/datasheet/usblc6-2.pdf)
