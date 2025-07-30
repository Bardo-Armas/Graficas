import io
import base64
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

class PDFGenerator:
    """Generador de PDFs con gráficas y tablas"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1f77b4')
        )
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#333333')
        )
    
    def create_pdf_with_chart_and_table(self, title, chart_fig, dataframe, filename, metrics=None):
        """
        Crear PDF con gráfica y tabla
        
        Args:
            title (str): Título del reporte
            chart_fig: Figura de Plotly
            dataframe (pd.DataFrame): DataFrame con los datos
            filename (str): Nombre del archivo
            metrics (dict): Métricas adicionales para mostrar
        
        Returns:
            bytes: Contenido del PDF en bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Contenido del PDF
        story = []
        
        # Título principal
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 20))
        
        # Información del reporte
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        info_text = f"<b>Fecha de generación:</b> {fecha_generacion}"
        story.append(Paragraph(info_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Métricas si se proporcionan
        if metrics:
            story.append(Paragraph("📊 Métricas Principales", self.subtitle_style))
            metrics_data = []
            for key, value in metrics.items():
                metrics_data.append([key, str(value)])
            
            metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e6e9ef'))
            ]))
            story.append(metrics_table)
            story.append(Spacer(1, 30))
        
        # Gráfica
        if chart_fig:
            story.append(Paragraph("📈 Gráfica", self.subtitle_style))
            
            # Convertir gráfica de Plotly a imagen
            img_bytes = chart_fig.to_image(format="png", width=600, height=400, scale=2)
            img = Image(io.BytesIO(img_bytes), width=5*inch, height=3.33*inch)
            story.append(img)
            story.append(Spacer(1, 30))
        
        # Tabla de datos
        if not dataframe.empty:
            story.append(Paragraph("📋 Datos Detallados", self.subtitle_style))
            
            # Preparar datos de la tabla
            table_data = []
            # Headers
            headers = list(dataframe.columns)
            table_data.append(headers)
            
            # Datos (limitar a 50 filas para evitar PDFs muy largos)
            df_limited = dataframe.head(50)
            for _, row in df_limited.iterrows():
                table_data.append([str(val) for val in row.values])
            
            # Crear tabla
            col_widths = [A4[0] / len(headers) - 20] * len(headers)
            table = Table(table_data, colWidths=col_widths)
            
            # Estilo de la tabla
            table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Data rows
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                
                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            
            story.append(table)
            
            # Nota si se limitaron las filas
            if len(dataframe) > 50:
                note = f"<i>Nota: Se muestran las primeras 50 filas de {len(dataframe)} registros totales.</i>"
                story.append(Spacer(1, 10))
                story.append(Paragraph(note, self.styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 30))
        footer_text = "Generado por Dashboard Profesional - Análisis de Datos"
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        story.append(Paragraph(footer_text, footer_style))
        
        # Construir PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def create_download_link(self, pdf_bytes, filename):
        """
        Crear enlace de descarga para el PDF
        
        Args:
            pdf_bytes (bytes): Contenido del PDF
            filename (str): Nombre del archivo
        
        Returns:
            str: HTML del enlace de descarga
        """
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📄 Descargar PDF</a>'
        return href

def create_pdf_download_button(title, chart_fig, dataframe, filename_base, metrics=None):
    """
    Crear botón de descarga de PDF con gráfica y tabla
    
    Args:
        title (str): Título del reporte
        chart_fig: Figura de Plotly
        dataframe (pd.DataFrame): DataFrame con los datos
        filename_base (str): Base del nombre del archivo
        metrics (dict): Métricas adicionales
    """
    pdf_generator = PDFGenerator()
    
    # Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_base}_{timestamp}.pdf"
    
    try:
        # Generar PDF
        pdf_bytes = pdf_generator.create_pdf_with_chart_and_table(
            title=title,
            chart_fig=chart_fig,
            dataframe=dataframe,
            filename=filename,
            metrics=metrics
        )
        
        # Crear botón de descarga
        st.download_button(
            label="📄 Descargar PDF (Gráfica + Datos)",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            help="Descarga un PDF con la gráfica y tabla de datos"
        )
        
    except Exception as e:
        st.error(f"Error al generar PDF: {str(e)}")
        st.info("Descarga disponible solo en formato CSV por el momento")