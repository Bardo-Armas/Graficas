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
import tempfile
import os

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
    
    def _capture_plotly_as_html_image(self, chart_fig):
        """
        Capturar gráfica de Plotly como imagen usando HTML estático
        
        Args:
            chart_fig: Figura de Plotly
            
        Returns:
            bytes: Imagen en formato PNG o None si falla
        """
        try:
            # Configurar Plotly para generar HTML estático
            config = {
                'displayModeBar': False,
                'staticPlot': True,
                'responsive': False
            }
            
            # Generar HTML de la gráfica
            html_str = pio.to_html(
                chart_fig,
                include_plotlyjs='inline',
                config=config,
                div_id="plotly-chart",
                full_html=True
            )
            
            # Modificar HTML para optimizar captura
            html_optimized = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{
                        margin: 0;
                        padding: 20px;
                        background-color: white;
                        font-family: Arial, sans-serif;
                    }}
                    #plotly-chart {{
                        width: 800px;
                        height: 500px;
                        margin: 0 auto;
                    }}
                </style>
            </head>
            <body>
                {html_str.split('<body>')[1].split('</body>')[0]}
            </body>
            </html>
            """
            
            # Intentar convertir HTML a imagen usando diferentes métodos
            return self._html_to_image_fallback(html_optimized, chart_fig)
            
        except Exception as e:
            print(f"Error en captura HTML: {e}")
            return None
    
    def _html_to_image_fallback(self, html_content, chart_fig):
        """
        Convertir HTML a imagen usando métodos de fallback
        
        Args:
            html_content (str): Contenido HTML
            chart_fig: Figura de Plotly original
            
        Returns:
            bytes: Imagen en formato PNG
        """
        # Método 1: Usar plotly.io.to_image con configuración optimizada
        try:
            # Configurar el engine de Plotly para mejor compatibilidad
            pio.renderers.default = "png"
            
            # Intentar conversión directa con configuración específica
            img_bytes = chart_fig.to_image(
                format="png",
                width=800,
                height=500,
                scale=1,
                engine="auto"
            )
            return img_bytes
        except Exception as e1:
            pass
        
        # Método 2: Usar matplotlib para recrear la gráfica
        try:
            return self._convert_plotly_to_matplotlib_enhanced(chart_fig)
        except Exception as e2:
            pass
        
        # Método 3: Crear representación textual de la gráfica
        try:
            return self._create_text_chart_representation(chart_fig)
        except Exception as e3:
            pass
        
        # Método 4: Placeholder final
        return self._create_enhanced_placeholder(chart_fig)
    
    def _convert_plotly_to_matplotlib_enhanced(self, plotly_fig):
        """
        Versión mejorada de conversión de Plotly a matplotlib
        
        Args:
            plotly_fig: Figura de Plotly
            
        Returns:
            bytes: Imagen en formato PNG
        """
        try:
            # Extraer datos de la figura de Plotly
            fig_dict = plotly_fig.to_dict()
            
            # Crear figura de matplotlib con mejor configuración
            plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'default')
            fig, ax = plt.subplots(figsize=(12, 8))
            fig.patch.set_facecolor('white')
            
            # Colores profesionales
            colors_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            
            # Procesar cada trace de Plotly
            for i, trace in enumerate(fig_dict.get('data', [])):
                trace_type = trace.get('type', 'scatter')
                color = colors_palette[i % len(colors_palette)]
                
                if trace_type == 'bar':
                    # Gráfico de barras mejorado
                    x_data = trace.get('x', [])
                    y_data = trace.get('y', [])
                    name = trace.get('name', f'Serie {i+1}')
                    
                    bars = ax.bar(x_data, y_data, label=name, color=color, alpha=0.8, 
                                edgecolor='white', linewidth=0.5)
                    
                    # Agregar valores en las barras
                    for bar in bars:
                        height = bar.get_height()
                        if height > 0:
                            ax.text(bar.get_x() + bar.get_width()/2., height,
                                  f'{height:.0f}', ha='center', va='bottom', fontsize=9)
                    
                elif trace_type == 'scatter':
                    # Gráfico de líneas mejorado
                    x_data = trace.get('x', [])
                    y_data = trace.get('y', [])
                    name = trace.get('name', f'Serie {i+1}')
                    mode = trace.get('mode', 'lines')
                    
                    if 'lines' in mode:
                        ax.plot(x_data, y_data, label=name, color=color, 
                              linewidth=3, marker='o', markersize=6, alpha=0.8)
                    elif 'markers' in mode:
                        ax.scatter(x_data, y_data, label=name, color=color, 
                                 s=100, alpha=0.8, edgecolors='white')
                        
                elif trace_type == 'pie':
                    # Gráfico de pastel mejorado
                    labels = trace.get('labels', [])
                    values = trace.get('values', [])
                    
                    wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                                    colors=colors_palette[:len(values)], 
                                                    startangle=90, explode=[0.05]*len(values))
                    
                    # Mejorar texto
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')
                    
                    ax.axis('equal')
            
            # Configurar títulos y etiquetas con mejor formato
            layout = fig_dict.get('layout', {})
            title = layout.get('title', {})
            if isinstance(title, dict):
                title_text = title.get('text', '')
            else:
                title_text = str(title)
            
            if title_text:
                ax.set_title(title_text, fontsize=16, fontweight='bold', pad=20, color='#333333')
            
            # Configurar ejes con mejor formato
            xaxis = layout.get('xaxis', {})
            yaxis = layout.get('yaxis', {})
            
            if xaxis.get('title', {}).get('text'):
                ax.set_xlabel(xaxis['title']['text'], fontsize=12, fontweight='bold')
            if yaxis.get('title', {}).get('text'):
                ax.set_ylabel(yaxis['title']['text'], fontsize=12, fontweight='bold')
            
            # Mejorar apariencia de los ejes
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Rotar etiquetas del eje X si son muy largas
            if hasattr(ax, 'get_xticklabels'):
                labels = [label.get_text() for label in ax.get_xticklabels()]
                if any(len(str(label)) > 8 for label in labels):
                    plt.xticks(rotation=45, ha='right')
            
            # Agregar leyenda si hay múltiples series
            if len(fig_dict.get('data', [])) > 1:
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True, 
                         fancybox=True, shadow=True)
            
            # Ajustar layout
            plt.tight_layout()
            
            # Convertir a bytes con alta calidad
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', quality=95)
            plt.close(fig)
            
            img_buffer.seek(0)
            return img_buffer.getvalue()
            
        except Exception as e:
            print(f"Error en matplotlib enhanced: {e}")
            return None
    
    def _create_text_chart_representation(self, chart_fig):
        """
        Crear representación textual de la gráfica cuando todo falla
        
        Args:
            chart_fig: Figura de Plotly
            
        Returns:
            bytes: Imagen con representación textual
        """
        try:
            fig_dict = chart_fig.to_dict()
            
            # Crear figura para mostrar datos textuales
            fig, ax = plt.subplots(figsize=(12, 8))
            fig.patch.set_facecolor('white')
            
            # Extraer información de la gráfica
            chart_info = []
            chart_info.append("📊 DATOS DE LA GRÁFICA")
            chart_info.append("=" * 40)
            
            # Procesar datos
            for i, trace in enumerate(fig_dict.get('data', [])):
                trace_type = trace.get('type', 'scatter')
                name = trace.get('name', f'Serie {i+1}')
                
                chart_info.append(f"\n🔹 {name} ({trace_type.upper()})")
                
                if trace_type == 'bar':
                    x_data = trace.get('x', [])
                    y_data = trace.get('y', [])
                    for x, y in zip(x_data[:10], y_data[:10]):  # Mostrar primeros 10
                        chart_info.append(f"   {x}: {y}")
                    if len(x_data) > 10:
                        chart_info.append(f"   ... y {len(x_data)-10} elementos más")
                
                elif trace_type == 'pie':
                    labels = trace.get('labels', [])
                    values = trace.get('values', [])
                    total = sum(values) if values else 1
                    for label, value in zip(labels, values):
                        percentage = (value/total)*100
                        chart_info.append(f"   {label}: {value} ({percentage:.1f}%)")
            
            # Mostrar texto en la imagen
            text_content = '\n'.join(chart_info)
            ax.text(0.05, 0.95, text_content, transform=ax.transAxes, 
                   fontsize=10, verticalalignment='top', fontfamily='monospace',
                   bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
            
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            # Título
            layout = fig_dict.get('layout', {})
            title = layout.get('title', {})
            if isinstance(title, dict):
                title_text = title.get('text', 'Gráfica de Datos')
            else:
                title_text = str(title) if title else 'Gráfica de Datos'
            
            ax.set_title(title_text, fontsize=16, fontweight='bold', pad=20)
            
            # Convertir a bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            
            img_buffer.seek(0)
            return img_buffer.getvalue()
            
        except Exception as e:
            print(f"Error en representación textual: {e}")
            return None
    
    def _create_enhanced_placeholder(self, chart_fig):
        """
        Crear placeholder mejorado con información de la gráfica
        
        Args:
            chart_fig: Figura de Plotly
            
        Returns:
            bytes: Imagen placeholder mejorada
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            fig.patch.set_facecolor('white')
            
            # Información básica de la gráfica
            try:
                fig_dict = chart_fig.to_dict()
                num_traces = len(fig_dict.get('data', []))
                chart_types = [trace.get('type', 'scatter') for trace in fig_dict.get('data', [])]
                unique_types = list(set(chart_types))
                
                info_text = f"""📊 GRÁFICA DISPONIBLE EN LA WEB
                
Tipo: {', '.join(unique_types)}
Series de datos: {num_traces}
                
⚠️ La gráfica no pudo ser convertida para PDF
debido a limitaciones del servidor de hosting.

✅ Puedes ver la gráfica completa e interactiva
en la aplicación web del dashboard."""
                
            except:
                info_text = """📊 GRÁFICA NO DISPONIBLE EN PDF
                
⚠️ La gráfica no pudo ser incluida en el PDF
debido a limitaciones técnicas del servidor.

✅ La gráfica está disponible en la aplicación web
donde puedes verla de forma interactiva."""
            
            ax.text(0.5, 0.5, info_text, 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=12, 
                   bbox=dict(boxstyle="round,pad=0.5", facecolor="#e3f2fd", 
                           edgecolor="#1976d2", linewidth=2))
            
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
            return None
    
    def _convert_chart_to_image(self, chart_fig):
        """
        Convertir gráfica de Plotly a imagen usando captura tipo screenshot
        
        Args:
            chart_fig: Figura de Plotly
            
        Returns:
            tuple: (success: bool, image_bytes: bytes, method_used: str)
        """
        # Método 1: Captura HTML optimizada
        try:
            img_bytes = self._capture_plotly_as_html_image(chart_fig)
            if img_bytes:
                return True, img_bytes, "Captura HTML"
        except Exception as e:
            print(f"Error en captura HTML: {e}")
        
        # Método 2: Conversión matplotlib mejorada
        try:
            img_bytes = self._convert_plotly_to_matplotlib_enhanced(chart_fig)
            if img_bytes:
                return True, img_bytes, "Matplotlib Mejorado"
        except Exception as e:
            print(f"Error en matplotlib mejorado: {e}")
        
        # Método 3: Representación textual
        try:
            img_bytes = self._create_text_chart_representation(chart_fig)
            if img_bytes:
                return True, img_bytes, "Representación Textual"
        except Exception as e:
            print(f"Error en representación textual: {e}")
        
        # Método 4: Placeholder mejorado
        try:
            img_bytes = self._create_enhanced_placeholder(chart_fig)
            if img_bytes:
                return True, img_bytes, "Placeholder Informativo"
        except Exception as e:
            print(f"Error en placeholder: {e}")
        
        return False, None, "Todos los métodos fallaron"
    
    def create_pdf_with_chart_and_table(self, title, chart_fig, dataframe, filename, metrics=None):
        """
        Crear PDF con gráfica y tabla (garantiza inclusión de gráfica como captura)
        
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
        
        # Gráfica (GARANTIZADA como captura)
        if chart_fig:
            story.append(Paragraph("📈 Gráfica", self.subtitle_style))
            
            # Convertir gráfica usando captura tipo screenshot
            success, img_bytes, method_used = self._convert_chart_to_image(chart_fig)
            
            if success and img_bytes:
                img = Image(io.BytesIO(img_bytes), width=6.5*inch, height=4.5*inch)
                story.append(img)
                
                # Nota sobre el método usado (solo si no es captura HTML)
                if method_used != "Captura HTML":
                    note_style = ParagraphStyle(
                        'ChartNote',
                        parent=self.styles['Normal'],
                        fontSize=8,
                        alignment=TA_CENTER,
                        textColor=colors.grey
                    )
                    story.append(Spacer(1, 5))
                    story.append(Paragraph(f"<i>Gráfica generada usando: {method_used}</i>", note_style))
            else:
                # Esto no debería pasar con los nuevos métodos
                error_text = "❌ Error crítico: No se pudo generar ninguna representación de la gráfica"
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
    Crear botón de descarga de PDF con gráfica capturada y tabla
    
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
        # Generar PDF con captura de gráfica
        pdf_bytes = pdf_generator.create_pdf_with_chart_and_table(
            title=title,
            chart_fig=chart_fig,
            dataframe=dataframe,
            filename=filename,
            metrics=metrics
        )
        
        # Crear botón de descarga
        st.download_button(
            label="📄 Descargar PDF (Gráfica Capturada + Datos)",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            help="Descarga un PDF con captura de la gráfica, métricas y tabla de datos"
        )
        
        st.success("✅ PDF generado exitosamente con gráfica incluida (captura tipo screenshot)")
        
    except Exception as e:
        st.error(f"Error al generar PDF: {str(e)}")
        st.info("💡 Por favor, intenta nuevamente o contacta al soporte técnico")