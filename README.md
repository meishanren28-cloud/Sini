# TENJO / vision

免费 Streamlit 日股尾盘筛选器，主要用于 **14:15 JST 左右**从候选池里找值得关注的尾盘埋伏对象。

功能：
- 只接受日本股票代码
- 读取 5 分钟盘中行情与日线
- 结合成交量、振幅、日内位置、短期趋势评分
- 显示可取得的新闻标题作为风险提示
- 不声称能够精准预测次日高低点

## 部署

把 `app.py`、`requirements.txt` 上传到 GitHub 仓库根目录。

Streamlit Community Cloud 中：
- Repository：你的 `vision`
- Branch：`main`
- Main file path：`app.py`

然后 Deploy 即可。

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```
