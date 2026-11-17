"""Namizna aplikacija za pretvorbo REK-1b v REK-O."""
import os
from pathlib import Path
import tempfile
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from converter import convert_file

class ConverterApp:
    def __init__(self, root):
        self.root = root
        self.source = None
        self.result = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        root.title('XML pretvornik • REK-1b → REK-O')
        root.geometry('720x430')
        root.minsize(620, 400)
        root.protocol('WM_DELETE_WINDOW', self.close)
        frame = ttk.Frame(root, padding=28)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='REK-1b → REK-O', font=('Segoe UI', 22, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='Izberi XML datoteko, jo pretvori in shrani rezultat.').pack(anchor='w', pady=(6, 24))
        self.open_button = ttk.Button(frame, text='1. Izberi XML datoteko …', command=self.select)
        self.open_button.pack(anchor='w')
        self.filename = tk.StringVar(value='Datoteka še ni izbrana.')
        ttk.Label(frame, textvariable=self.filename, wraplength=620).pack(anchor='w', pady=(10, 20))
        actions = ttk.Frame(frame)
        actions.pack(anchor='w')
        self.convert_button = ttk.Button(actions, text='2. Pretvori', command=self.convert, state='disabled')
        self.convert_button.pack(side='left', padx=(0, 12))
        self.save_button = ttk.Button(actions, text='3. Shrani kot …', command=self.save, state='disabled')
        self.save_button.pack(side='left')
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=(24, 12))
        self.status = tk.StringVar(value='Pripravljeno.')
        ttk.Label(frame, textvariable=self.status, wraplength=620).pack(anchor='w')
        ttk.Label(frame, text='Zneski se prenesejo iz starega obrazca brez seštevanja.\nVeljavnost po XSD shemi eDavki ni preverjena.', foreground='#555555').pack(anchor='w', pady=(20, 0))

    def select(self):
        path = filedialog.askopenfilename(title='Izberi vhodni REK-1b XML', filetypes=[('XML datoteke', '*.xml'), ('Vse datoteke', '*.*')])
        if path:
            self.source = Path(path)
            self.result = None
            self.filename.set(str(self.source))
            self.convert_button.config(state='normal')
            self.save_button.config(state='disabled')
            self.status.set('Datoteka je izbrana. Klikni Pretvori.')

    def convert(self):
        self.result = None
        for button in (self.open_button, self.convert_button, self.save_button):
            button.config(state='disabled')
        self.progress.start()
        self.status.set('Pretvarjam …')
        self.future = self.executor.submit(convert_file, self.source)
        self.root.after(100, self.poll)

    def poll(self):
        if not self.future.done():
            self.root.after(100, self.poll)
            return
        self.progress.stop()
        self.open_button.config(state='normal')
        self.convert_button.config(state='normal')
        try:
            self.result, count = self.future.result()
        except Exception as exc:
            self.status.set('Pretvorba ni uspela. Preveri vhodno datoteko.')
            messagebox.showerror('Napaka pri pretvorbi', str(exc))
        else:
            self.save_button.config(state='normal')
            self.status.set(f'Pretvorba je uspela. Število postavk: {count}. Rezultat lahko shraniš.')

    def save(self):
        path = filedialog.asksaveasfilename(title='Shrani pretvorjeni REK-O', initialfile=self.source.stem + '_REK_O.xml', defaultextension='.xml', filetypes=[('XML datoteke', '*.xml')])
        if not path:
            return
        destination = Path(path)
        if destination.resolve() == self.source.resolve() or (destination.exists() and os.path.samefile(destination, self.source)):
            messagebox.showerror('Izberi drugo ime', 'Izhodna datoteka ne sme prepisati vhodne datoteke.')
            return
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
                temporary = stream.name
                stream.write(self.result)
            os.replace(temporary, destination)
        except OSError as exc:
            messagebox.showerror('Napaka pri shranjevanju', str(exc))
        else:
            self.status.set(f'Shranjeno: {destination}')
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

    def close(self):
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()

if __name__ == '__main__':
    window = tk.Tk()
    ConverterApp(window)
    window.mainloop()
