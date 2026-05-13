# Fake GPS App

Python + Kivy 開發的 Android 模擬定位工具。

## 功能

- 地圖點擊釘選虛擬 GPS 位置（OpenStreetMap）
- 地址 / 座標搜尋
- 長按地圖標記手動編輯經緯度
- 虛擬搖桿控制移動方向
- 速度滑桿（1～200 km/h）+ 快速預設按鈕
- Android Foreground Service 背景持續注入 Mock Location

## 桌面開發環境

```bash
pip install -r requirements.txt
python main.py
```

> 桌面環境無 Pyjnius，Mock Location 橋接會自動降級為 stub（僅 log 輸出）。

## 打包 Android APK

需要在 **Linux / WSL / macOS** 環境執行 Buildozer：

```bash
# 安裝 Buildozer
pip install buildozer

# 首次打包（會下載 Android SDK/NDK，需要時間）
buildozer android debug

# APK 輸出位置
# bin/fakegps-1.0.0-arm64-v8a-debug.apk
```

## Android 裝置設定

1. 開啟「開發人員選項」
2. 選取「模擬位置應用程式」→ 選擇 **Fake GPS**
3. 安裝 APK 後開啟 App，點擊「開始模擬」

## 專案結構

```
fake-gps-app/
├── main.py                        # App 入口，整合所有元件
├── buildozer.spec                 # Android 打包設定
├── requirements.txt               # 桌面開發依賴
├── logic/
│   ├── app_state.py               # 共享狀態 dataclass
│   ├── location_logic.py          # 球面幾何座標計算
│   ├── geocoder.py                # Nominatim 地址搜尋
│   └── mock_location_bridge.py    # Pyjnius Android 橋接
├── ui/
│   ├── main_screen.kv             # 主畫面 KV 佈局
│   ├── map_widget.py              # OSM 地圖元件
│   ├── joystick_widget.py         # 虛擬搖桿
│   ├── speed_panel.py             # 速度滑桿面板
│   ├── search_bar.py              # 搜尋列
│   └── coord_edit_popup.py        # 座標編輯 Popup
├── android/
│   └── MockLocationService.java   # Android Foreground Service
└── tests/
    └── test_location_logic.py     # 座標計算單元測試
```
