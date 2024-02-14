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

    # Search for elements with any of the footnote-related class names
    footnote_tags = soup.find_all(True, class_=lambda x: x and any(cls in x.split() for cls in ['footnotepara', 'footnote', 'Footnote-Reference', 'footnote1', 'note', 'footnote-anchor', 'footnotePara']))

    # Check if any footnote tags were found and log the findings
    if footnote_tags:
        logging.info(f'CONFIRMED: {len(footnote_tags)} footnote tags found in {file_path}')
        for tag in footnote_tags:
            a_tag = tag.find('a')
            parent_tag = tag.find_parent(['p', 'h2'])  # Find the parent <p> or <h2> tag if it exists.

            if a_tag and 'id' in a_tag.attrs and not a_tag.find_parent('aside'):
                logging.info(f'Found <a> with id: {a_tag["id"]} in {file_path}, ready to wrap.')
            elif parent_tag and 'id' in parent_tag.attrs and not parent_tag.find_parent('aside'):
                logging.info(f'Found parent tag with id: {parent_tag["id"]} in {file_path}, ready to wrap.')
            else:
                logging.info(f'No suitable wrapping conditions met for tag in {file_path}.')
    else:
        logging.info(f'UNCONFIRMED: No footnote tags found in {file_path}')



    for tag in footnote_tags:
        a_tag = tag.find('a')
        p_tag = tag.find_parent('p')  # Find the parent <p> tag if it exists.
        h2_tag = tag.find_parent('h2')  # Find the parent <h2> tag if it exists.
        
        # First condition: If <a> tag has an 'id', wrap its parent (<p> or <h2>) with an <aside> if not already wrapped.
        if a_tag and 'id' in a_tag.attrs and not a_tag.find_parent('aside'):
            parent_tag = p_tag or h2_tag
            if parent_tag:
                fn_id = a_tag['id']
                aside_tag = soup.new_tag('aside', **{'epub:type': 'footnote', 'id': fn_id})
                parent_tag.wrap(aside_tag)
                modified = True
                logging.info(f'Footnote {fn_id} wrapped in <aside> in file {file_path}')
                
        # Second condition: If <a> tag doesn't have an 'id' but its parent <p> has, and it's not already wrapped in an <aside>.
        elif a_tag and not 'id' in a_tag.attrs and p_tag and 'id' in p_tag.attrs and not p_tag.find_parent('aside'):
            fn_id = p_tag['id']
            aside_tag = soup.new_tag('aside', **{'epub:type': 'footnote', 'id': fn_id})
            p_tag.wrap(aside_tag)
            modified = True
            logging.info(f'Footnote {fn_id} wrapped in <aside> in file {file_path}')

        # Third condition: If <a> tag doesn't have an 'id' but its parent <h2> has, and it's not already wrapped in an <aside>.
        elif a_tag and not 'id' in a_tag.attrs and h2_tag and 'id' in h2_tag.attrs and not h2_tag.find_parent('aside'):
            fn_id = h2_tag['id']
            aside_tag = soup.new_tag('aside', **{'epub:type': 'footnote', 'id': fn_id})
            h2_tag.wrap(aside_tag)
            modified = True
            logging.info(f'Footnote {fn_id} wrapped in <aside> in file {file_path}')
        else:
            logging.info(f'No appropriate tag with id found in {file_path} or already wrapped in <aside>')


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
            if item.filename.endswith('.xhtml') and ('footnote' in item.filename.lower() or 'fn' in item.filename.lower()):
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
