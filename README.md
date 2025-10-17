# native_web_ui

Undergraduate student-led project to explore what's possible with native Web user intefaces. We are curious if this might be a replacement for the PyQt5-based PhysiCell Studio desktop application. But besides that, it seems like worthwhile knowledge and skils for students to have, if they are interested in Web design and HCI.

Two of the more popular native Web UI frameworks with a Python API are https://streamlit.io/ vs. https://www.gradio.app/ .

## Fork this repo into your own github.com account

<img src="./images/fork_repo.png" width="60%">


## Goals
* what are some example applications where these UIs are used?
* how do these two frameworks differ (at a high level)?
* demonstrate some very simple UIs, starting with Streamlit.

## Questions (related to PhysiCell Studio)
* what interactive plotting packages are possible to use within Streamlit (or Gradio)?

## Demos
* after installing streamlit:
```
cd streamlit
streamlit run cells_demo1.py
```
If you click the `Run the machine` button, it will plot a random set of circles. We want to be able to read circles (centers, radius) from a file and plot those.
