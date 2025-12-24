import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SISTEMA CHIFA - POS", layout="wide")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        width: 100%;
        height: 60px;
        font-weight: bold;
        border-radius: 10px;
    }
    .total-box {
        font-size: 30px;
        font-weight: bold;
        color: #d32f2f;
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border: 2px solid #d32f2f;
    }
</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A GOOGLE SHEETS ---
def init_connection():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    # Abre la hoja "Pedidos Chifa"
    sheet = client.open("Pedidos Chifa").sheet1
    return sheet

try:
    sheet = init_connection()
except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
    st.stop()

# --- DATOS DEL MENÚ ---
MENU = {
    "CHAUFAS": {
        "Chaufa de Pollo": 15.00,
        "Chaufa de Carne": 18.00,
        "Chaufa Especial": 22.00,
        "Chaufa Aeropuerto": 20.00
    },
    "TALLARINES": {
        "Tallarín Saltado Pollo": 16.00,
        "Tallarín Saltado Carne": 19.00,
        "Tallarín Sam Si": 24.00
    },
    "FUERTES / ESPECIALES": {
        "Pollo Ti Pa Kay": 22.00,
        "Pollo Chi Jau Kay": 22.00,
        "Kam Lu Wantán": 28.00,
        "Chancho con Piña": 24.00
    },
    "SOPAS": {
        "Sopa Wantán Simple": 10.00,
        "Sopa Wantán Especial": 18.00,
        "Sopa Fuchifú": 15.00
    },
    "BEBIDAS": {
        "Inca Kola 500ml": 4.00,
        "Coca Cola 500ml": 4.00,
        "Chicha Morada (Jarra)": 12.00
    }
}

# --- ESTADO DE LA SESIÓN (CARRITO) ---
if 'cart' not in st.session_state:
    st.session_state.cart = []

# --- LÓGICA DE INTERFAZ ---
st.title("🍜 SISTEMA DE VENTAS - CHIFA")

col_menu, col_cart = st.columns([2, 1])

with col_menu:
    st.subheader("Menú del Día")
    tabs = st.tabs(list(MENU.keys()))
    
    for i, category in enumerate(MENU.keys()):
        with tabs[i]:
            items = MENU[category]
            cols = st.columns(2)
            for idx, (item, price) in enumerate(items.items()):
                with cols[idx % 2]:
                    with st.container():
                        st.write(f"**{item}**")
                        st.write(f"S/. {price:.2f}")
                        
                        # Selector de cantidad y botón para agregar al carrito
                        qty = st.number_input(f"Cant.", min_value=1, value=1, key=f"qty_{item}")
                        
                        if st.button(f"AÑADIR - S/. {price:.2f}", key=f"btn_{item}"):
                            # Agregar al carrito
                            st.session_state.cart.append({
                                "ITEM": item,
                                "PRECIO": price,
                                "CANTIDAD": int(qty),
                                "TOTAL": price * qty
                            })
                            st.toast(f"✅ Agregado: {item} x {qty}")

with col_cart:
    st.subheader("🛒 La Cuenta")
    
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        # Mostrar carrito
        st.dataframe(df_cart[["ITEM", "CANTIDAD", "TOTAL"]], use_container_width=True, hide_index=True)
        
        grand_total = df_cart["TOTAL"].sum()
        
        st.markdown(f'<div class="total-box">TOTAL: S/. {grand_total:.2f}</div>', unsafe_allow_html=True)
        st.write("")
        
        if st.button("✅ REGISTRAR VENTA", type="primary", use_container_width=True):
            with st.spinner("Registrando venta..."):
                now = datetime.now()
                fecha = now.strftime("%Y-%m-%d")
                hora = now.strftime("%H:%M:%S")
                
                rows_to_add = []
                for item in st.session_state.cart:
                    # Estructura: FECHA, HORA, CANTIDAD, ITEM, PRECIO, TOTAL
                    row = [
                        fecha,
                        hora,
                        item["CANTIDAD"],
                        item["ITEM"],
                        item["PRECIO"],
                        item["TOTAL"]
                    ]
                    rows_to_add.append(row)
                
                try:
                    sheet.append_rows(rows_to_add)
                    st.success("¡Venta registrada con éxito!")
                    st.session_state.cart = [] # Limpiar carrito
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar en Google Sheets: {e}")
        
        if st.button("🗑️ Limpiar Carrito", use_container_width=True):
            st.session_state.cart = []
            st.rerun()
    else:
        st.info("El carrito está vacío. Selecciona productos a la izquierda.")

# --- HISTÓRICO RECIENTE ---
st.divider()
with st.expander("Ver Histórico de Ventas"):
    try:
        data = sheet.get_all_records()
        if data:
            st.dataframe(pd.DataFrame(data).tail(10), use_container_width=True)
        else:
            st.write("No hay datos registrados aún.")
    except Exception as e:
        st.write(f"No hay datos visibles (Asegúrate de tener encabezados en la hoja): {e}")
