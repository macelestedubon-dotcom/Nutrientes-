import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- CONSTANTES DE NUTRIENTES ---
CARGAS_ELEMENTO = {"K": 1, "Ca": 2, "Mg": 2, "Na": 1}
PESO_ATOMICO = {"K": 39.0, "Ca": 40.0, "Mg": 24.3, "Na": 23.0}
NUTRIENTES_PPM = ["P", "Fe", "Cu", "Zn", "Mn"]

# 1. Configuración de la plataforma
st.set_page_config(
    page_title="Dashboard de Suelos y Encalado", 
    page_icon="🌱", 
    layout="wide"
)

st.title("🌱 Dashboard Interactivo: Optimización de Suelos")
st.markdown("Gestión de enmiendas y cuantificación de nutrientes según reportes de laboratorio. Por Gudiel Yoj :-)")
st.divider()

# 2. Barra lateral para parámetros globales
st.sidebar.header("⚙️ Parámetros de la Parcela")

# Opción para calcular el peso de la parcela o ingresarlo manualmente
calcular_peso = st.sidebar.checkbox("Calcular peso a partir de dimensiones", value=False)

if calcular_peso:
    st.sidebar.markdown("**Parámetros de campo:**")
    densidad = st.sidebar.number_input("Densidad aparente (g/cm³):", min_value=0.1, max_value=2.0, value=1.2, step=0.1)
    area = st.sidebar.number_input("Área de la parcela (m²):", min_value=1.0, value=10000.0, step=1000.0, help="1 ha = 10,000 m²")
    profundidad = st.sidebar.number_input("Profundidad (m):", min_value=0.01, max_value=1.0, value=0.20, step=0.05)
    
    # Cálculo: Área (m2) * Profundidad (m) * Densidad (t/m3) * 1000 (kg/t)
    # Nota: g/cm3 es numéricamente igual a t/m3
    peso_parcela = area * profundidad * densidad * 1000
    st.sidebar.success(f"⚖️ Peso calculado: **{peso_parcela:,.0f} kg**")
else:
    peso_parcela = st.sidebar.number_input(
        "Peso de la capa arable (kg):", 
        min_value=500000.0, 
        max_value=10000000.0, 
        value=2000000.0, 
        step=100000.0,
        help="Por defecto, 2,000,000 kg equivale a 1 ha a 20 cm de profundidad con densidad de 1.0 g/cm³."
    )

# 3. Organización de la interfaz en Pestañas (Tabs)
tab1, tab2, tab3 = st.tabs([
    "📊 Cálculo de Encalado", 
    "📈 Análisis Multicriterio (PRNT)", 
    "🧪 Cálculo de Nutrientes"
])

# --- PESTAÑA 1: CÁLCULO INDIVIDUAL DE ENCALADO ---
with tab1:
    col_in, col_out = st.columns([1, 2])
    
    with col_in:
        st.subheader("📥 Datos de Acidez")
        acidez = st.number_input(
            "Acidez de cambio (cmol_c/dm³):", 
            min_value=0.0, 
            max_value=15.0, 
            value=1.5, 
            step=0.1
        )
        prnt = st.slider(
            "PRNT de la enmienda comercial (%):", 
            min_value=10, 
            max_value=100, 
            value=85, 
            step=5
        )
        
        # Lógica matemática original recalculada con el nuevo peso de parcela
        kg_cal = (acidez * 100 * peso_parcela) / 200000
        kg_ajustado = (kg_cal * 100) / prnt
        ton_ajustado = kg_ajustado / 1000

    with col_out:
        st.subheader("🎯 Recomendación Específica")
        
        kpi1, kpi2 = st.columns(2)
        kpi1.metric(label="Requerimiento Neto", value=f"{kg_ajustado:,.2f} kg")
        kpi2.metric(label="Equivalente Comercial", value=f"{ton_ajustado:,.2f} t")
        
        if ton_ajustado > 0:
            st.info(
                f"💡 **Nota de campo:** Para incorporar **{ton_ajustado:,.2f} toneladas**, asegúrese de realizar la "
                "aplicación de manera uniforme y con una anticipación mínima de 30 a 45 días antes de la siembra."
            )
            if ton_ajustado > 4.0:
                st.warning(
                    "⚠️ **Alerta técnica:** La dosis supera las 4 toneladas. Se recomienda fraccionar la "
                    "aplicación en dos etapas para evitar desequilibrios biológicos."
                )

# --- PESTAÑA 2: ANÁLISIS MULTICRITERIO ---
with tab2:
    st.subheader("📉 Sensibilidad del Requerimiento según la Calidad del PRNT")
    st.markdown("Visualización de la variación de la dosis total requerida según la calidad de la cal.")
    
    rango_prnt = np.arange(40, 105, 5)
    dosis_simuladas = [(kg_cal * 100) / p for p in rango_prnt]
    
    df_simulacion = pd.DataFrame({
        'PRNT (%)': rango_prnt,
        'Dosis Comercial (kg)': dosis_simuladas
    })
    
    fig_prnt = px.line(
        df_simulacion, 
        x='PRNT (%)', 
        y='Dosis Comercial (kg)',
        markers=True,
        title=f"Curva de Encalado para Acidez de {acidez} cmol_c/dm³",
        labels={'Dosis Comercial (kg)': 'Dosis Requerida (kg)'}
    )
    fig_prnt.update_traces(line_color='#2d6a2d', marker=dict(size=8))
    fig_prnt.update_layout(hovermode="x unified")
    
    st.plotly_chart(fig_prnt, use_container_width=True)

# --- PESTAÑA 3: CÁLCULO DE NUTRIENTES ---
with tab3:
    st.subheader("🧪 Cuantificación Total de Nutrientes en la Parcela")
    st.markdown(f"Calculando para un peso de suelo de: **{peso_parcela:,.0f} kg**")
    
    col_cmol, col_ppm = st.columns(2)
    resultados_nutrientes = []

    # 1. Entrada y cálculo para elementos en cmol(+)/kg
    with col_cmol:
        st.markdown("#### Bases Intercambiables (cmol(+)/kg)")
        for elem in CARGAS_ELEMENTO.keys():
            val = st.number_input(f"{elem}:", min_value=0.0, value=1.0, step=0.1, key=f"in_{elem}")
            
            # Fórmula: cmol(+)/kg a gramos = (cmol * Peso Atómico) / (Carga * 100)
            # Para pasarlo a kg en toda la parcela: (Gramos_por_kg * Peso_parcela) / 1000
            peso_at = PESO_ATOMICO[elem]
            carga = CARGAS_ELEMENTO[elem]
            
            kg_total = (val * peso_at * peso_parcela) / (carga * 100000)
            resultados_nutrientes.append({
                "Elemento": elem, 
                "Concentración": val, 
                "Unidad": "cmol(+)/kg", 
                "Total en Parcela (kg)": round(kg_total, 2)
            })

    # 2. Entrada y cálculo para elementos en ppm (mg/kg)
    with col_ppm:
        st.markdown("#### Micro/Macronutrientes (ppm o mg/kg)")
        for elem in NUTRIENTES_PPM:
            val = st.number_input(f"{elem}:", min_value=0.0, value=15.0, step=1.0, key=f"in_{elem}")
            
            # Fórmula: ppm = mg/kg. Para pasarlo a kg: (ppm * Peso_parcela) / 1,000,000
            kg_total = (val * peso_parcela) / 1000000
            resultados_nutrientes.append({
                "Elemento": elem, 
                "Concentración": val, 
                "Unidad": "ppm", 
                "Total en Parcela (kg)": round(kg_total, 2)
            })

    # Visualización de resultados de nutrientes
    st.divider()
    df_nutrientes = pd.DataFrame(resultados_nutrientes)
    
    col_tab_nutr, col_graf_nutr = st.columns([1, 2])
    
    with col_tab_nutr:
        st.dataframe(df_nutrientes, use_container_width=True, hide_index=True)
        
    with col_graf_nutr:
        fig_nutrientes = px.bar(
            df_nutrientes, 
            x="Elemento", 
            y="Total en Parcela (kg)", 
            color="Unidad",
            text="Total en Parcela (kg)",
            title="Cantidad de Elementos Disponibles (kg en parcela)"
        )
        fig_nutrientes.update_traces(textposition='outside')
        st.plotly_chart(fig_nutrientes, use_container_width=True)

# 4. Documentación de las fórmulas embebidas en el footer
st.markdown("---")
with st.expander("🔬 Ver Fundamentos Matemáticos del Modelo"):
    st.markdown("### 1. Encalado")
    st.latex(r"Dosis_{base}\ (kg) = \frac{Acidez \times 100 \times Peso_{parcela}}{200,000}")
    st.latex(r"Dosis_{Ajustada}\ (kg) = \frac{Dosis_{base} \times 100}{PRNT}")
    
    st.markdown("### 2. Nutrientes en ppm (mg/kg)")
    st.markdown("Se basa en la relación directa de peso:")
    st.latex(r"Total\ (kg) = \frac{ppm \times Peso_{parcela}\ (kg)}{1,000,000}")
    
    st.markdown("### 3. Nutrientes en cmol(+)/kg")
    st.markdown("Requiere transformar las cargas a unidades de masa usando el peso atómico:")
    st.latex(r"Total\ (kg) = \frac{cmol(+)/kg \times Peso\ At\acute{o}mico \times Peso_{parcela}\ (kg)}{Carga \times 100,000}")