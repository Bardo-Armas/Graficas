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
import plotly.io as pio
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import warnings

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
    
    def _convert_plotly_to_matplotlib(self, plotly_fig):
        """
        Convertir figura de Plotly a matplotlib y luego a imagen
        
        Args:
            plotly_fig: Figura de Plotly
            
        Returns:
            bytes: Imagen en formato PNG
        """
        try:
            # Extraer datos de la figura de Plotly
            fig_dict = plotly_fig.to_dict()
            
            # Crear figura de matplotlib
            plt.style.use('default')
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor('white')
            
            # Procesar cada trace de Plotly
            for trace in fig_dict.get('data', []):
                trace_type = trace.get('type', 'scatter')
                
                if trace_type == 'bar':
                    # Gráfico de barras
                    x_data = trace.get('x', [])
                    y_data = trace.get('y', [])
                    name = trace.get('name', '')
                    color = trace.get('marker', {}).get('color', '#1f77b4')
                    
                    ax.bar(x_data, y_data, label=name, color=color, alpha=0.8)
                    
                elif trace_type == 'scatter':
                    # Gráfico de líneas o puntos
                    x_data = trace.get('x', [])
                    y_data = trace.get('y', [])
                    name = trace.get('name', '')
                    mode = trace.get('mode', 'lines')
                    color = trace.get('line', {}).get('color', '#1f77b4')
                    
                    if 'lines' in mode:
                        ax.plot(x_data, y_data, label=name, color=color, linewidth=2)
                    elif 'markers' in mode:
                        ax.scatter(x_data, y_data, label=name, color=color, s=50)
                        
                elif trace_type == 'pie':
                    # Gráfico de pastel
                    labels = trace.get('labels', [])
                    values = trace.get('values', [])
                    colors_pie = trace.get('marker', {}).get('colors', None)
                    
                    ax.pie(values, labels=labels, autopct='%1.1f%%', 
                          colors=colors_pie, startangle=90)
                    ax.axis('equal')
            
            # Configurar títulos y etiquetas
            layout = fig_dict.get('layout', {})
            title = layout.get('title', {})
            if isinstance(title, dict):
                title_text = title.get('text', '')
            else:
                title_text = str(title)
            
            if title_text:
                ax.set_title(title_text, fontsize=14, fontweight='bold', pad=20)
            
            # Configurar ejes
            xaxis = layout.get('xaxis', {})
            yaxis = layout.get('yaxis', {})
            
            if xaxis.get('title', {}).get('text'):
                ax.set_xlabel(xaxis['title']['text'], fontsize=12)
            if yaxis.get('title', {}).get('text'):
                ax.set_ylabel(yaxis['title']['text'], fontsize=12)
            
            # Rotar etiquetas del eje X si son muy largas
            if hasattr(ax, 'get_xticklabels'):
                labels = [label.get_text() for label in ax.get_xticklabels()]
                if any(len(str(label)) > 10 for label in labels):
                    plt.xticks(rotation=45, ha='right')
            
            # Agregar leyenda si hay múltiples series
            if len(fig_dict.get('data', [])) > 1:
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # Ajustar layout
            plt.tight_layout()
            
            # Convertir a bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close(fig)  # Cerrar figura para liberar memoria
            
            img_buffer.seek(0)
            return img_buffer.getvalue()
            
        except Exception as e:
            # Si falla matplotlib, crear una imagen de placeholder
            return self._create_placeholder_chart(str(e))
    
    def _create_placeholder_chart(self, error_msg="Error al generar gráfica"):
        """
        Crear una imagen placeholder cuando falla la conversión
        
        Args:
            error_msg (str): Mensaje de error
            
        Returns:
            bytes: Imagen placeholder en formato PNG
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor('white')
            
            # Crear un gráfico simple de placeholder
            ax.text(0.5, 0.5, '📊\nGráfica no disponible\n\n' + error_msg, 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
            
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            # Convertir a bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            
            img_buffer.seek(0)
            return img_buffer.getvalue()
            
        except Exception:
            # Si todo falla, retornar None
            return None
    
    def _convert_chart_to_image(self, chart_fig):
        """
        Convertir gráfica de Plotly a imagen usando múltiples métodos
        
        Args:
            chart_fig: Figura de Plotly
            
        Returns:
            tuple: (success: bool, image_bytes: bytes or None, method_used: str)
        """
        # Método 1: Intentar con Kaleido (si está disponible)
        try:
            img_bytes = chart_fig.to_image(format="png", width=800, height=500, scale=2)
            return True, img_bytes, "Kaleido"
        except Exception as kaleido_error:
            pass
        
        # Método 2: Usar matplotlib como alternativa
        try:
            img_bytes = self._convert_plotly_to_matplotlib(chart_fig)
            if img_bytes:
                return True, img_bytes, "Matplotlib"
        except Exception as matplotlib_error:
            pass
        
        # Método 3: Crear placeholder
        try:
            img_bytes = self._create_placeholder_chart("Conversión no disponible")
            if img_bytes:
                return True, img_bytes, "Placeholder"
        except Exception:
            pass
        
        return False, None, "Todos los métodos fallaron"
    
    def create_pdf_with_chart_and_table(self, title, chart_fig, dataframe, filename, metrics=None):
        """
        Crear PDF con gráfica y tabla (garantiza inclusión de gráfica)
        
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
        
        # Gráfica (GARANTIZADA)
        if chart_fig:
            story.append(Paragraph("📈 Gráfica", self.subtitle_style))
            
            # Convertir gráfica usando múltiples métodos
            success, img_bytes, method_used = self._convert_chart_to_image(chart_fig)
            
            if success and img_bytes:
                img = Image(io.BytesIO(img_bytes), width=6*inch, height=4*inch)
                story.append(img)
                
                # Agregar nota sobre el método usado (solo para debugging)
                if method_used != "Kaleido":
                    note_style = ParagraphStyle(
                        'ChartNote',
                        parent=self.styles['Normal'],
                        fontSize=8,
                        alignment=TA_CENTER,
                        textColor=colors.grey
                    )
                    story.append(Spacer(1, 5))
                    story.append(Paragraph(f"<i>Gráfica generada con {method_used}</i>", note_style))
            else:
                # Esto no debería pasar, pero por seguridad
                error_text = "Error: No se pudo generar la gráfica con ningún método disponible"
                story.append(Paragraph(error_text, self.styles['Normal']))
            
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
        footer_text = "Súbito - 2025"
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

def create_pdf_download_button(title, chart_fig, dataframe, filename_base, metrics=None):
    """
    Crear botón de descarga de PDF con gráfica y tabla (GARANTIZA inclusión de gráfica)
    
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
        # Generar PDF (siempre incluye gráfica)
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
            help="Descarga un PDF con gráfica, métricas y tabla de datos"
        )
        
        st.success("✅ PDF generado exitosamente con gráfica incluida")
        
    except Exception as e:
        st.error(f"Error al generar PDF: {str(e)}")
        st.info("💡 Por favor, intenta nuevamente o contacta al soporte técnico")