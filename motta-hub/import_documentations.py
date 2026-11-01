import argparse
import hashlib
import importlib.util
import io
import json
import logging
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT / 'documentation-source'
DEFAULT_OUTPUT = ROOT
WORD = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
MAX_XML = 50 * 1024 * 1024
REVIEWED_EXAMPLES = {
    'api/sql/sql-api-full-documentation.md': 'e3c3840f91f99836ae17f018c5c8e7cf3684b6d0d9f7a073dc2aad33348f7588',
    'first-year/ux/prototipo-figma/auditoria/invariantes.json': 'b24ff3d533a6c0c6106edb37a46d4f5e19a7590e4e368946c2d23e78314c1a3d',
}


class HTMLText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1
        if tag in ('p', 'div', 'br', 'li', 'tr', 'h1', 'h2', 'h3'):
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden = max(0, self.hidden - 1)
        if tag in ('p', 'div', 'li', 'tr', 'h1', 'h2', 'h3'):
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def normalize(text):
    return text.replace('\r\n', '\n').replace('\r', '\n').replace('\x00', '').strip()


def decode_text(data):
    for encoding in ('utf-8-sig', 'utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8', 'cp1252'):
        try:
            return data.decode(encoding)
        except UnicodeError:
            pass
    raise ValueError('text_encoding')


def credentials(text):
    categories = set()
    patterns = {
        'private_key': r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
        'provider_token': r'\b(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{15,}|sk-(?:proj-)?[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{30,})\b',
        'jwt': r'\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]{10,}\b',
        'credential_url': r'(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|https?)://[^\s/:<>]+:([^\s/@<>]+)@',
        'bearer_token': r'(?i)\bBearer\s+([A-Za-z0-9_.-]{16,})',
        'credential_assignment': r'''(?im)^[ \t]*(?:(?:private|public|static|final|const|let|var|String)[ \t]+)*["']?(?:[A-Za-z]+[_-])?(?:password|passwd|senha|api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|secret[_-]?key|jwt[_-]?secret)["']?[ \t]*(?::|=(?!=))[ \t]*["'`]?([^\s"'`,;}]+)''',
    }
    for category, pattern in patterns.items():
        for match in re.finditer(pattern, text):
            value = match.group(1) if match.lastindex else match.group(0)
            # Explicit placeholders are not credentials; ambiguous literals block copying.
            if match.lastindex and (value.startswith(('<', '${', '{{', 'process.env.', 'System.getenv', 'os.environ', 'dotenv.get(')) or re.search(r'(?i)(example|exemplo|placeholder|redacted|sua[_-]|seu[_-]|your[_-]|changeme|REPLACE|^xxx|^\*+$)', value)):
                continue
            if match.lastindex and value.lower() in ('string', 'null', 'none', 'true', 'false', 'required', 'obrigatorio', 'obrigatório', 'varchar', 'text'):
                continue
            categories.add(category)
    return sorted(categories)


def docx_text(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if sum(info.file_size for info in archive.infolist()) > MAX_XML:
            raise ValueError('docx_size_limit')
        texts, audit, headings = [], [], []
        names = sorted(name for name in archive.namelist() if name.endswith('.xml'))
        for name in names:
            raw = archive.read(name)
            if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
                raise ValueError('unsafe_xml')
            root = ET.fromstring(raw)
            audit.append(''.join(root.itertext()))
            if name != 'word/document.xml' and not re.fullmatch(r'word/(?:header\d+|footer\d+|footnotes|endnotes)\.xml', name):
                continue
            paragraphs = []
            for paragraph in root.iter(WORD + 'p'):
                parts = []
                for node in paragraph.iter():
                    if node.tag == WORD + 't':
                        parts.append(node.text or '')
                    elif node.tag == WORD + 'tab':
                        parts.append('\t')
                    elif node.tag in (WORD + 'br', WORD + 'cr'):
                        parts.append('\n')
                text = ''.join(parts)
                paragraphs.append(text)
                style = paragraph.find(WORD + 'pPr/' + WORD + 'pStyle')
                if name == 'word/document.xml' and style is not None and re.search(r'(?i)(heading|title|titulo|título)', style.get(WORD + 'val', '')) and text.strip():
                    headings.append(text.strip())
            if name == 'word/document.xml':
                texts.insert(0, '\n'.join(paragraphs))
            else:
                texts.append('\n'.join(paragraphs))
    return normalize('\n\n'.join(texts)), '\n'.join(audit), headings[0] if headings else ''


def pdf_backend():
    if shutil.which('pdftotext'):
        return 'pdftotext'
    for module in ('pypdf', 'PyPDF2', 'fitz'):
        if importlib.util.find_spec(module):
            return module
    if sys.platform == 'darwin' and shutil.which('swift'):
        return 'swift-pdfkit'
    return 'unavailable'


def pdf_text(path, backend):
    if backend == 'pdftotext':
        result = subprocess.run(['pdftotext', '-enc', 'UTF-8', str(path), '-'], capture_output=True, timeout=120, check=True)
        return normalize(result.stdout.decode('utf-8'))
    if backend in ('pypdf', 'PyPDF2'):
        module = __import__(backend)
        reader = module.PdfReader(str(path))
        return normalize('\n\n'.join(page.extract_text() or '' for page in reader.pages))
    if backend == 'fitz':
        import fitz
        with fitz.open(path) as document:
            return normalize('\n\n'.join(page.get_text() for page in document))
    if backend == 'swift-pdfkit':
        code = '''import Foundation
import PDFKit
let url = URL(fileURLWithPath: CommandLine.arguments[1])
guard let doc = PDFDocument(url: url) else { exit(2) }
for i in 0..<doc.pageCount { print(doc.page(at: i)?.string ?? "") }
'''
        with tempfile.TemporaryDirectory(prefix='documentation-pdf-') as directory:
            script = Path(directory) / 'extract.swift'
            script.write_text(code, encoding='utf-8')
            result = subprocess.run(['swift', str(script), str(path)], capture_output=True, timeout=120, check=True)
        return normalize(result.stdout.decode('utf-8'))
    raise ValueError('pdf_converter_unavailable')


def title_for(content, path, heading=''):
    if heading:
        return heading
    lines = content.splitlines()
    fenced = False
    for index, line in enumerate(lines):
        if re.match(r'^\s*(```|~~~)', line):
            fenced = not fenced
        if fenced:
            continue
        match = re.match(r'^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$', line)
        if match:
            return match[1].strip()
        if line.strip() and index + 1 < len(lines) and re.fullmatch(r'\s*(?:={3,}|-{3,})\s*', lines[index + 1]):
            return line.strip()
    return path.stem if path.suffix else path.name


def import_documents(source, output, dry_run=False):
    source, output = Path(source).resolve(), Path(output).resolve()
    if not source.is_dir() or not output.is_dir():
        raise ValueError('source_or_output_missing')
    if source == output or source in output.parents:
        raise ValueError('source_output_overlap')
    logging.getLogger('pypdf').setLevel(logging.CRITICAL)
    schemas = sorted(item.name for item in source.iterdir() if item.is_dir() and not item.is_symlink())
    backend = pdf_backend()
    documents, copies, issues, blocked = [], [], [], []
    originals = hashlib.sha256()
    for schema in schemas:
        for path in sorted((source / schema).rglob('*'), key=lambda p: p.relative_to(source).as_posix()):
            relative = path.relative_to(source).as_posix()
            if path.is_symlink():
                blocked.append({'path': relative, 'category': 'symlink_not_allowed'})
                continue
            if not path.is_file():
                continue
            data = path.read_bytes()
            originals.update(relative.encode('utf-8') + b'\0' + hashlib.sha256(data).digest())
            suffix = path.suffix.lower()
            format_name = {'.md': 'md', '.markdown': 'md', '.txt': 'text', '': 'text', '.pdf': 'pdf', '.docx': 'docx', '.html': 'html', '.htm': 'html'}.get(suffix, suffix.lstrip('.') or 'text')
            content, heading, audit = '', '', data.decode('latin-1')
            try:
                if format_name == 'pdf':
                    content = pdf_text(path, backend)
                    audit += '\n' + content
                    if not content:
                        issues.append({'path': relative, 'category': 'pdf_without_text'})
                elif format_name == 'docx':
                    content, xml_audit, heading = docx_text(data)
                    audit += '\n' + xml_audit
                elif format_name in ('md', 'text', 'html'):
                    text = decode_text(data)
                    audit += '\n' + text
                    content = text
                    if format_name == 'html':
                        parser = HTMLText()
                        parser.feed(text)
                        content = normalize(''.join(parser.parts))
                elif format_name in ('css', 'js', 'cjs', 'json', 'jsp', 'java', 'py', 'svg'):
                    content = decode_text(data)
                    audit += '\n' + content
                else:
                    # Static binary assets keep their original links, never fabricated text.
                    issues.append({'path': relative, 'category': 'binary_asset_without_text'})
            except Exception as error:
                # Never print converter errors: they may contain source data.
                issues.append({'path': relative, 'category': 'extraction_failed_' + type(error).__name__})
                blocked.append({'path': relative, 'category': 'unscanned_extraction_failure'})
            # Reviewed examples: environment-variable placeholders and a numeric fixture field; exact hashes keep each exemption scoped to the reviewed content.
            # Exact source hashes ensure this exemption cannot hide future source changes.
            reviewed = REVIEWED_EXAMPLES.get(relative)
            findings = credentials(audit)
            if reviewed and hashlib.sha256(data).hexdigest() == reviewed:
                findings = [category for category in findings if category != 'credential_assignment']
            for category in findings:
                blocked.append({'path': relative, 'category': category})
            if not content and format_name in ('md', 'text', 'docx', 'html'):
                issues.append({'path': relative, 'category': 'empty_text'})
            documents.append({'id': hashlib.sha256(relative.encode('utf-8')).hexdigest(), 'schema': schema,
                              'title': title_for(content, path, heading), 'content': content,
                              'sourcePath': relative, 'sourceUrl': '/documentation-files/' + '/'.join(quote(part, safe='') for part in path.relative_to(source).parts),
                              'format': format_name})
            copies.append((relative, data))
    report = {'schemas': schemas, 'documents': len(documents), 'byType': dict(sorted(Counter(doc['format'] for doc in documents).items())),
              'bySchema': {schema: dict(sorted(Counter(doc['format'] for doc in documents if doc['schema'] == schema).items())) for schema in schemas},
              'pdfBackend': backend, 'issues': issues, 'securityFindings': blocked, 'sourceDigest': originals.hexdigest(), 'written': False}
    if blocked or dry_run:
        return report
    files_root = output / 'documentation-files'
    json_path = output / 'documentations.json'
    if files_root.is_symlink() or json_path.is_symlink():
        raise ValueError('output_symlink_not_allowed')
    payload = json.dumps({'schemas': schemas, 'documents': documents}, ensure_ascii=False, indent=2) + '\n'
    # Verify collisions before writing; never overwrite unrelated existing sources.
    for relative, data in copies:
        destination = files_root / relative
        if any(parent.is_symlink() for parent in destination.parents) or destination.is_symlink():
            raise ValueError('output_symlink_not_allowed')
        if destination.exists() and destination.read_bytes() != data:
            raise ValueError('existing_source_copy_differs')
    for schema in schemas:
        (files_root / schema).mkdir(parents=True, exist_ok=True)
    for relative, data in copies:
        destination = files_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            destination.write_bytes(data)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=output, prefix='.documentations-', suffix='.json', delete=False) as temporary:
        temporary.write(payload)
        temporary_path = Path(temporary.name)
    temporary_path.replace(json_path)
    report['written'] = True
    report['jsonSha256'] = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    return report


def main():
    parser = argparse.ArgumentParser(description='Importação local somente leitura das fontes; não executa documentos.')
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        report = import_documents(args.source, args.output, args.dry_run)
    except Exception as error:
        print(json.dumps({'errorCategory': type(error).__name__}, ensure_ascii=False))
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if report['securityFindings'] else 0


if __name__ == '__main__':
    sys.exit(main())

