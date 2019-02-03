import glob
import nbformat
from nbconvert import PythonExporter

def convert_notebook(notebook_path, module_path):
    with open(notebook_path) as fh:
        nb = nbformat.reads(fh.read(), nbformat.NO_CONVERT)

    exporter = PythonExporter()
    source, _ = exporter.from_notebook_node(nb)

    with open(module_path, 'w+') as fh:
        fh.write(source)

    print("\t> Converted {} to {}".format(notebook_path, module_path))


if __name__ == '__main__':
    # Root level
    for fnotebook in glob.glob('/instance/code/*.ipynb'):
        fname = fnotebook[:-5] + 'py'
        convert_notebook(fnotebook, fname)

    # Subfolders
    for fnotebook in glob.glob('/instance/code/**/*.ipynb'):
        fname = fnotebook[:-5] + 'py'
        convert_notebook(fnotebook, fname)
