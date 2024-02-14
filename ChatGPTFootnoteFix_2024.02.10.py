import os
import logging
import zipfile
from bs4 import BeautifulSoup
from io import BytesIO

# Configure logging
logging.basicConfig(filename='footnote_modification.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Search for footnotes
def modify_footnotes_in_html(content, file_path):
    soup = BeautifulSoup(content, 'html.parser')
    modified = False

    footnote_tags = soup.find_all(True, class_=lambda x: x and any(cls in x.split() for cls in ['footnotepara', 'footnote', 'Footnote-Reference', 'footnote1', 'note', 'footnote-anchor', 'footnotePara']))

    if footnote_tags:
        logging.info(f'CONFIRMED: {len(footnote_tags)} footnote tags found in {file_path}')
        for tag in footnote_tags:
            # Check for an <a> tag within a <span> and then find the parent <p> or <h2> tag
            a_tag = tag.find('a')
            span_tag = a_tag.find_parent('span') if a_tag else None
            parent_tag = span_tag.find_parent(['p', 'h2']) if span_tag else None
            
            if span_tag and parent_tag and 'id' in parent_tag.attrs and not parent_tag.find_parent('aside'):
                logging.info(f'Found <span> wrapped <a> with parent {parent_tag.name} having id: {parent_tag["id"]} in {file_path}, ready to wrap.')
            elif a_tag and 'id' in a_tag.attrs and not a_tag.find_parent('aside'):
                logging.info(f'Found <a> with id: {a_tag["id"]} in {file_path}, ready to wrap.')
            elif parent_tag and 'id' in parent_tag.attrs and not parent_tag.find_parent('aside'):
                logging.info(f'Found parent tag with id: {parent_tag["id"]} in {file_path}, ready to wrap.')
            else:
                logging.info(f'No suitable wrapping conditions met for tag in {file_path}.')
    else:
        logging.info(f'UNCONFIRMED: No footnote tags found in {file_path}')

    # Iterate over the tags to apply the new logic
    for tag in footnote_tags:
        a_tag = tag.find('a')
        span_tag = a_tag.find_parent('span') if a_tag else None
        parent_tag = span_tag.find_parent(['p', 'h2']) if span_tag else None

        if parent_tag and 'id' in parent_tag.attrs and not parent_tag.find_parent('aside'):
            # Now wrapping the parent <p> or <h2> tag with an <aside>
            fn_id = parent_tag['id']
            aside_tag = soup.new_tag('aside', **{'epub:type': 'footnote', 'id': fn_id})
            parent_tag.wrap(aside_tag)
            modified = True
            logging.info(f'Footnote {fn_id} wrapped in <aside> in file {file_path}')

        # The existing conditions for wrapping <a> tags directly or their <p>/<h2> parents without <span> can remain unchanged

    if modified:
        logging.info(f'Footnotes modified in {file_path}')
        return str(soup)
    else:
        logging.info(f'No modifications needed in {file_path}')
        return None


def process_epub_file(epub_path, output_dir):
    # Temporary storage for modified files
    memory_zip = BytesIO()

    with zipfile.ZipFile(epub_path, 'r') as zin, zipfile.ZipFile(memory_zip, 'a', zipfile.ZIP_DEFLATED, False) as zout:
        for item in zin.infolist():
            content = zin.read(item.filename)
            if item.filename.endswith('.xhtml') or item.filename.endswith('.html'):
                logging.info(f'Found XHTML file: {item.filename} in {epub_path}')
                modified_content = modify_footnotes_in_html(content, item.filename)
                if modified_content:
                    zout.writestr(item, modified_content)
                else:
                    zout.writestr(item, content)
            else:
                zout.writestr(item, content)

    # Define the output file path
    output_file_path = os.path.join(output_dir, os.path.basename(epub_path))
    
    # Write the new EPUB to the output directory
    with open(output_file_path, 'wb') as f:
        f.write(memory_zip.getvalue())

def process_epub_directory(directory_path, output_dir):
    if not os.path.exists(directory_path):
        logging.error(f'Directory does not exist: {directory_path}')
        return

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    logging.info(f'Starting processing in directory: {directory_path}')

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith('.epub'):
                epub_path = os.path.join(root, file)
                logging.info(f'Processing EPUB file: {epub_path}')
                process_epub_file(epub_path, output_dir)
            else:
                logging.info(f'Skipped file: {file}')

# Set the directory path and output directory path
directory_path = r'C:\Users\whyno\Resilio Sync\Ebook Editing\Input'
output_directory_path = r'C:\Users\whyno\Resilio Sync\Ebook Editing\Output'
process_epub_directory(directory_path, output_directory_path)
