import zipfile
import xml.etree.ElementTree as ET
import os

def extract_text_from_docx(file_path):
    try:
        doc = zipfile.ZipFile(file_path)
        xml_content = doc.read('word/document.xml')
        doc.close()
        tree = ET.XML(xml_content)
        
        paragraphs = []
        for paragraph in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            texts = [node.text for node in paragraph.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
            if texts:
                paragraphs.append(''.join(texts))
        
        return '\n'.join(paragraphs)
    except Exception as e:
        return str(e)

def extract_text_from_pptx(file_path):
    try:
        doc = zipfile.ZipFile(file_path)
        slide_texts = []
        for name in doc.namelist():
            if name.startswith('ppt/slides/slide') and name.endswith('.xml'):
                xml_content = doc.read(name)
                tree = ET.XML(xml_content)
                texts = [node.text for node in tree.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t') if node.text]
                if texts:
                    slide_texts.append(' '.join(texts))
        return '\n---\n'.join(slide_texts)
    except Exception as e:
        return str(e)

files = [
    'documentation/MCA_Project Report_format.docx',
    'documentation/SRP-Abstract.docx',
    'documentation/meeting_assistant_comp.docx',
    'documentation/presentation_02.pptx'
]

with open('documentation/extracted_texts.txt', 'w', encoding='utf-8') as out:
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        out.write(f'=== {f} ===\n')
        if ext == '.docx':
            out.write(extract_text_from_docx(f) + '\n')
        elif ext == '.pptx':
            out.write(extract_text_from_pptx(f) + '\n')
        out.write('\n========================================\n\n')
