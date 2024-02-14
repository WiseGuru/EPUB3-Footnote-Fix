import os
import logging
import zipfile
from bs4 import BeautifulSoup
from io import BytesIO

# Configure logging
logging.basicConfig(filename='footnote_modification.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def modify_footnotes_in_html(content, file_path):
    soup = BeautifulSoup(content, 'html.parser')
    modified = False

    footnote_tags = soup.find_all(True, {'class': ['footnotepara', 'footnote']})
    if not footnote_tags:
        logging.info(f'No footnote tags found in {file_path}')

    for tag in footnote_tags:
        a_tag = tag.find('a')
        if a_tag and 'id' in a_tag.attrs and not tag.find_parent('aside', {'epub:type': 'footnote'}):
            fn_id = a_tag['id']
            aside_tag = soup.new_tag('aside', **{'epub:type': 'footnote', 'id': fn_id})
            tag.wrap(aside_tag)
            modified = True
            logging.info(f'Footnote {fn_id} wrapped in <aside> in file {file_path}')
        else:
            logging.info(f'No appropriate <a> tag with id found in {file_path} or already wrapped in <aside>')

    if modified:
        logging.info(f'Footnotes modified in {file_path}')
        return str(soup)
    else:
        logging.info(f'No modifications needed in {file_path}')
        return None

def process_epub_file(epub_path):
    # Temporary storage for modified files
    memory_zip = BytesIO()

    with zipfile.ZipFile(epub_path, 'r') as zin, zipfile.ZipFile(memory_zip, 'a', zipfile.ZIP_DEFLATED, False) as zout:
        for item in zin.infolist():
            content = zin.read(item.filename)
            if item.filename.endswith('.xhtml') and ('footnote' in item.filename.lower() or 'fn' in item.filename.lower()):
                logging.info(f'Found XHTML file: {item.filename} in {epub_path}')
                modified_content = modify_footnotes_in_html(content, item.filename)
                if modified_content:
                    zout.writestr(item, modified_content)
                else:
                    zout.writestr(item, content)
            else:
                zout.writestr(item, content)

    # Replace old EPUB with the new one
    with open(epub_path, 'wb') as f:
        f.write(memory_zip.getvalue())

def process_epub_directory(directory_path):
    if not os.path.exists(directory_path):
        logging.error(f'Directory does not exist: {directory_path}')
        return
    logging.info(f'Starting processing in directory: {directory_path}')

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith('.epub'):
                epub_path = os.path.join(root, file)
                logging.info(f'Processing EPUB file: {epub_path}')
                process_epub_file(epub_path)
            else:
                logging.info(f'Skipped file: {file}')

# Set the directory path
directory_path = r'C:\Users\whyno\Resilio Sync\Ebook Editing\Input'
process_epub_directory(directory_path)
