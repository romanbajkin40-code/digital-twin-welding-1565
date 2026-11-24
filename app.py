import math
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Цифровой двойник лазерной сварки 1565", layout="wide")
st.title("Цифровой двойник лазерной сварки сплава 1565")
st.caption("Исследовательский симулятор для планирования опытов — не система назначения безопасных режимов.")

def calculate(x):
    P, v, vp = x["power"], x["speed"], x["wire_speed"]
    d, rho = 1.0, x["rho"]
    E = 0.06 * P / v
    Aw = math.pi * d**2 / 4
    Q = Aw * (1000 * vp)
    mass = rho * Q / 1000
    q = Q / (1000 * v)
    f = x["area_deposit"] / (x["area_base"] + x["area_deposit"])
    cmix = (1-f)*x["mg_base"] + f*x["mg_wire"]
    cafter = cmix * (1-x["loss"])
    return dict(energy_J_mm=E, wire_area_mm2=Aw, wire_volume_mm3_min=Q,
                wire_mass_g_min=mass, wire_per_length_mm3_mm=q,
                filler_fraction=f, mg_mixed_wt_pct=cmix, mg_after_loss_wt_pct=cafter)

def validate(x):
    errors=[]
    for key in ("thickness","power","speed","wire_speed","rho","area_deposit","area_base"):
        if x[key] <= 0: errors.append(f"Параметр «{key}» должен быть больше нуля.")
    if x["power"] > 1500: errors.append("Мощность превышает ограничение 1500 Вт.")
    if not 1 <= x["thickness"] <= 6 or abs(x["thickness"]*2-round(x["thickness"]*2)) > 1e-8:
        errors.append("Толщина должна быть от 1 до 6 мм с шагом 0,5 мм.")
    for key in ("mg_base","mg_wire"):
        if not 0 <= x[key] <= 100: errors.append(f"{key}: содержание Mg должно быть в диапазоне 0–100 мас. %.")
    if not 0 <= x["loss"] <= 1: errors.append("Коэффициент потерь Mg должен быть от 0 до 1.")
    if x["frequency"] < 0 or x["wobble_width"] < 0: errors.append("Параметры Wobble не могут быть отрицательными.")
    return errors

if "history" not in st.session_state:
    st.session_state.history = []

st.sidebar.header("Исходные данные")
with st.sidebar:
    thickness=st.select_slider("Толщина листа, мм", options=[1+i*0.5 for i in range(11)], value=3.0)
    joint=st.selectbox("Тип соединения", ["Стыковое","Нахлёсточное"])
    power=st.number_input("Средняя мощность, Вт", min_value=1.0, max_value=2000.0, value=1000.0, step=50.0)
    speed=st.number_input("Скорость сварки, м/мин", min_value=0.001, value=0.6, step=0.05, format="%.3f")
    wire_speed=st.number_input("Подача проволоки, м/мин", min_value=0.001, value=1.2, step=0.1, format="%.3f")
    mg_base=st.number_input("Mg основного металла, мас. %", min_value=0.0, max_value=100.0, value=4.5, step=0.1)
    mg_wire=st.number_input("Mg проволоки, мас. %", min_value=0.0, max_value=100.0, value=5.0, step=0.1)
    wobble_width=st.number_input("Ширина/амплитуда Wobble, мм", min_value=0.0, value=2.0, step=0.1)
    frequency=st.number_input("Частота Wobble, Гц", min_value=0.0, value=100.0, step=5.0)
    gas=st.selectbox("Защитный газ", ["Аргон","Гелий","Смесь Ar/He","Другое"])
    st.divider()
    st.subheader("Сценарные допущения")
    area_base=st.number_input("Эффективная площадь основного металла, мм²", min_value=0.001, value=1.8, step=0.1)
    area_deposit=st.number_input("Эффективная площадь присадки, мм²", min_value=0.001, value=0.6, step=0.1)
    loss=st.slider("Сценарная относительная потеря Mg, λ", 0.0, 0.5, 0.05, 0.01)

x=dict(thickness=thickness,joint=joint,power=power,speed=speed,wire_speed=wire_speed,
       mg_base=mg_base,mg_wire=mg_wire,wobble_width=wobble_width,frequency=frequency,
       gas=gas,rho=2.65,area_base=area_base,area_deposit=area_deposit,loss=loss)
errors=validate(x)
if errors:
    for e in errors: st.error(e)
    st.stop()

r=calculate(x)
st.subheader("Расчётные показатели")
cols=st.columns(4)
metrics=[
    ("Погонная энергия",f'{r["energy_J_mm"]:.2f} Дж/мм'),
    ("Объёмная подача",f'{r["wire_volume_mm3_min"]:.2f} мм³/мин'),
    ("Массовая подача",f'{r["wire_mass_g_min"]:.3f} г/мин'),
    ("Подача на длину",f'{r["wire_per_length_mm3_mm"]:.3f} мм³/мм')]
for c,(label,value) in zip(cols,metrics): c.metric(label,value)

a,b,c=st.columns(3)
a.metric("Сечение проволоки",f'{r["wire_area_mm2"]:.4f} мм²')
b.metric("Доля присадки (сценарий)",f'{100*r["filler_fraction"]:.1f} %')
c.metric("Отношение подачи проволоки / сварки",f'{wire_speed/speed:.2f}')
st.subheader("Баланс магния — сценарная оценка")
m1,m2=st.columns(2)
m1.metric("Mg после идеализированного смешения",f'{r["mg_mixed_wt_pct"]:.3f} мас. %')
m2.metric("Mg после заданной сценарной потери",f'{r["mg_after_loss_wt_pct"]:.3f} мас. %')
st.info("Доля присадки рассчитана только из введённых эффективных площадей. Коэффициент λ — учебное допущение, а не измеренный закон испарения Mg.")

st.subheader("Карта режимов: мощность — скорость сварки")
st.caption("Цвет показывает только расчётную погонную энергию. Это не карта риска и не граница бездефектных режимов.")
pvals=np.linspace(100,1500,36)
vvals=np.linspace(0.1,2.0,36)
rows=[{"Мощность, Вт":pp,"Скорость, м/мин":vv,"Погонная энергия, Дж/мм":0.06*pp/vv}
      for pp in pvals for vv in vvals]
df=pd.DataFrame(rows)
fig=px.density_heatmap(df,x="Скорость, м/мин",y="Мощность, Вт",z="Погонная энергия, Дж/мм",
                       nbinsx=36,nbinsy=36,color_continuous_scale="Viridis")
fig.add_scatter(x=[speed],y=[power],mode="markers+text",text=["Текущий расчёт"],
                textposition="top center",marker=dict(size=12,color="red",symbol="x"))
st.plotly_chart(fig,use_container_width=True)

st.subheader("Сохранение сценария")
if st.button("Добавить текущий вариант в журнал"):
    record={**x,**r,"timestamp":datetime.now().isoformat(timespec="seconds")}
    st.session_state.history.append(record)
    st.success(f"Вариант сохранён. В журнале: {len(st.session_state.history)}")
if st.session_state.history:
    hist=pd.DataFrame(st.session_state.history)
    st.dataframe(hist,use_container_width=True)
    st.download_button("Скачать журнал CSV",hist.to_csv(index=False).encode("utf-8-sig"),
                       "welding_scenarios.csv","text/csv")
else:
    st.caption("Журнал пока пуст. Добавьте варианты; сохраняется не менее 10 и более сценариев.")

st.subheader("Принятые формулы и допущения")
st.markdown("""
- Погонная энергия: **E = 0,06 · P / v**, Дж/мм; это энергия на единицу длины, не поглощённая энергия.
- Сечение проволоки: **A = πd²/4**, где d = 1,0 мм.
- Объёмная подача: **Q = A · (1000 · vпр)**, мм³/мин.
- Массовая подача: **ṁ = ρ · Q / 1000**, г/мин; принято ρ = 2,65 г/см³.
- Подача на длину: **q = Q / (1000 · v)**, мм³/мм.
- Доля присадки: **f = Aприс/(Aосн + Aприс)** по введённым эффективным площадям.
- **Cmix = (1 − f)Cосн + fCпр**; **Cafter = Cmix(1 − λ)**.
""")
with st.expander("Ограничения модели — обязательно к прочтению"):
    st.warning("""
    Программа является исследовательским симулятором, а не системой автоматического назначения режимов.
    Без экспериментальной калибровки глубина проплавления, пористость, потери Mg и стабильность процесса не прогнозируются достоверно.
    Нельзя трактовать области карты как «низкий риск»: цвет кодирует только расчётную погонную энергию.
    Отсутствие дефектов не гарантируется. Скорость ручной сварки должна измеряться экспериментально.
    Тип газа, Wobble и допустимые настройки необходимо сверять с паспортом фактически установленной комплектации.
    Программа не управляет лазером. Физические опыты — только в оборудованной лаборатории, обученным персоналом и по утверждённой инструкции.
    """)
