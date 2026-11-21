"""Ilustraciones propias de los Temas de interés (SVG planos, sin fotos de terceros).

Lo ejecuta construir.py. Cada tema elige una clave en su encabezado («imagen: ninez»);
la ilustración toma el color de la materia del tema. Motivo escalonado como en las portadas.

Claves disponibles: ninez, mujer, beneficios, asistencia, usucapion, propiedad, denuncia,
discriminacion, discapacidad, animales, divorcio, defensa, herencia, alquiler, deudas, juicio, cobro, desalojo, contrato, compraventa, danos. Una clave desconocida usa «defensa».
"""

COLOR_MATERIA = {
    'Constitucional': '#24497F', 'Laboral': '#1F5B44', 'Familia': '#6B3A7D', 'Civil': '#1E6B73',
    'Procesal civil': '#154C52', 'Penal': '#A3241B', 'Procesal penal': '#741B14', 'Administrativa': '#4A5868',
    'Agraria': '#5A6B1F', 'Tributario': '#8A5A0F', 'Personas con discapacidad': '#3B4FA3', 'Comercial': '#5B4636', 'Otras': '#55615A',
}
_OC = '#E0B04A'
_W = '#FFFFFF'


def _esc_ilus(y, paso=8, alto=3, ancho=400):
    """Franja escalonada (motivo de las portadas) que sube y baja a lo largo de y."""
    d, x, nivel, sube = [f'M0 {y}'], 0, 0, True
    while x < ancho:
        x += paso
        nivel += 1 if sube else -1
        d.append(f'H{x}V{y - nivel * paso}')
        if nivel in (alto, 0):
            sube = not sube
    d.append(f'V{y + 40}H0Z')
    return ''.join(d)


def _pers_ilus(cx, cab, r, alto, fill=_W, op=1):
    """Figura humana simple: cabeza y cuerpo redondeado."""
    hombro = cab + r + 6
    ancho = r * 1.55
    return (f'<circle cx="{cx}" cy="{cab}" r="{r}" fill="{fill}" opacity="{op}"/>'
            f'<path d="M{cx - ancho} {hombro + alto}V{hombro + ancho * .7}Q{cx - ancho} {hombro} {cx} {hombro}Q{cx + ancho} {hombro} {cx + ancho} {hombro + ancho * .7}V{hombro + alto}Z" fill="{fill}" opacity="{op}"/>')


def _casa_ilus(x, y, w, puerta=_OC, fill=_W):
    h = w * .72
    return (f'<path d="M{x} {y + w * .42}L{x + w / 2} {y}L{x + w} {y + w * .42}V{y + w * .42 + h}H{x}Z" fill="{fill}"/>'
            f'<rect x="{x + w * .4}" y="{y + w * .42 + h * .45}" width="{w * .2}" height="{h * .55}" rx="3" fill="{puerta}"/>'
            f'<rect x="{x + w * .14}" y="{y + w * .5}" width="{w * .18}" height="{w * .16}" rx="2" fill="{puerta}" opacity=".55"/>')


def _fig_ilus(clave, c):
    if clave == 'ninez':
        libro = (f'<path d="M248 150l40-10v44l-40 10z" fill="{_W}"/><path d="M328 150l-40-10v44l40 10z" fill="{_W}" opacity=".85"/>'
                 f'<path d="M288 140v44" stroke="{_OC}" stroke-width="4"/><path d="M256 160l24-6M256 170l24-6M296 154l24 6M296 164l24 6" stroke="{c}" stroke-width="3" opacity=".5"/>')
        return _pers_ilus(140, 82, 17, 78) + _pers_ilus(200, 104, 13, 58, _OC) + libro
    if clave == 'mujer':
        escudo = (f'<path d="M282 60l46 16v40c0 34-22 54-46 64-24-10-46-30-46-64V76z" fill="{_OC}"/>'
                  f'<path d="M262 118l14 14 28-30" fill="none" stroke="{_W}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>')
        mujer = (f'<circle cx="162" cy="78" r="19" fill="{_W}"/>'
                 f'<path d="M162 102c-18 0-26 12-30 30l-14 56h88l-14-56c-4-18-12-30-30-30z" fill="{_W}"/>')
        return mujer + escudo
    if clave == 'beneficios':
        mal = (f'<rect x="104" y="96" width="150" height="96" rx="12" fill="{_W}"/><path d="M152 96v-14a8 8 0 018-8h38a8 8 0 018 8v14" fill="none" stroke="{_W}" stroke-width="9"/>'
               f'<rect x="104" y="128" width="150" height="8" fill="{c}" opacity=".35"/><rect x="168" y="120" width="22" height="24" rx="4" fill="{_OC}"/>')
        mon = ''.join(f'<ellipse cx="306" cy="{186 - k * 14}" rx="30" ry="9" fill="{_OC}" stroke="{c}" stroke-opacity=".35" stroke-width="2"/>' for k in range(6))
        return mal + mon
    if clave == 'asistencia':
        mano = f'<path d="M168 150q18 6 30-4" fill="none" stroke="{_W}" stroke-width="7" stroke-linecap="round"/>'
        return _pers_ilus(150, 78, 18, 96) + _pers_ilus(214, 116, 12, 60, _OC) + mano + _casa_ilus(272, 86, 80, c)
    if clave == 'usucapion':
        reloj = (f'<path d="M282 64h60M282 190h60" stroke="{_OC}" stroke-width="9" stroke-linecap="round"/>'
                 f'<path d="M292 68h40l-20 59 20 59h-40l20-59z" fill="none" stroke="{_W}" stroke-width="6" stroke-linejoin="round"/>'
                 f'<path d="M298 182l14-30 14 30zM302 84h20l-10 26z" fill="{_OC}"/>')
        return _casa_ilus(96, 70, 140, c) + reloj
    if clave == 'propiedad':
        llave = (f'<circle cx="290" cy="104" r="26" fill="none" stroke="{_OC}" stroke-width="12"/>'
                 f'<path d="M290 130v62M290 160h20M290 178h14" stroke="{_OC}" stroke-width="12" stroke-linecap="round"/>')
        cerca = ''.join(f'<path d="M{x} 200v-34l7-8 7 8v34z" fill="{_W}" opacity=".45"/>' for x in range(70, 250, 22))
        return cerca + _casa_ilus(110, 64, 120, c) + llave
    if clave == 'denuncia':
        hoja = (f'<path d="M110 52h96l30 30v122H110z" fill="{_W}"/><path d="M206 52v30h30" fill="{c}" opacity=".25"/>'
                + ''.join(f'<rect x="128" y="{y}" width="{w}" height="7" rx="3" fill="{c}" opacity=".45"/>' for y, w in ((98, 88), (116, 70), (134, 88), (152, 56))))
        burbuja = (f'<path d="M262 70h72a14 14 0 0114 14v54a14 14 0 01-14 14h-44l-22 22v-22h-6a14 14 0 01-14-14V84a14 14 0 0114-14z" fill="{_OC}"/>'
                   f'<rect x="293" y="86" width="10" height="36" rx="5" fill="{_W}"/><circle cx="298" cy="136" r="6" fill="{_W}"/>')
        return hoja + burbuja
    if clave == 'discriminacion':
        igual = f'<rect x="168" y="44" width="64" height="11" rx="5" fill="{_OC}"/><rect x="168" y="64" width="64" height="11" rx="5" fill="{_OC}"/>'
        gente = (_pers_ilus(110, 118, 15, 66) + _pers_ilus(170, 112, 15, 72, _OC) + _pers_ilus(230, 118, 15, 66, _W, .75) + _pers_ilus(290, 112, 15, 72))
        return igual + gente
    if clave == 'discapacidad':
        silla = (f'<circle cx="186" cy="74" r="15" fill="{_W}"/>'
                 f'<path d="M180 98v42h40l14 40" fill="none" stroke="{_W}" stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/>'
                 f'<path d="M182 116h32" stroke="{_W}" stroke-width="11" stroke-linecap="round"/>'
                 f'<path d="M158 128a40 40 0 1062 36" fill="none" stroke="{_W}" stroke-width="10" stroke-linecap="round"/>')
        rampa = f'<path d="M262 200l92-58v58z" fill="{_OC}"/><path d="M262 200l92-58" stroke="{_W}" stroke-width="4" opacity=".6"/>'
        return silla + rampa
    if clave == 'animales':
        pata = (f'<ellipse cx="170" cy="150" rx="40" ry="34" fill="{_W}"/>'
                + ''.join(f'<ellipse cx="{x}" cy="{y}" rx="15" ry="20" transform="rotate({r} {x} {y})" fill="{_W}"/>'
                          for x, y, r in ((116, 104, -25), (148, 78, -8), (192, 78, 8), (224, 104, 25))))
        corazon = f'<path d="M296 170c-40-26-52-44-52-62a24 24 0 0152-8 24 24 0 0152 8c0 18-12 36-52 62z" fill="{_OC}"/>'
        return pata + corazon
    if clave == 'divorcio':
        anillos = (f'<circle cx="150" cy="124" r="40" fill="none" stroke="{_W}" stroke-width="12"/>'
                   f'<circle cx="250" cy="124" r="40" fill="none" stroke="{_OC}" stroke-width="12"/>'
                   f'<path d="M200 70v20M200 158v20" stroke="{_W}" stroke-width="5" stroke-linecap="round" stroke-dasharray="2 10" opacity=".7"/>')
        hoja = f'<rect x="300" y="82" width="58" height="76" rx="6" fill="{_W}" opacity=".9"/>' + ''.join(f'<rect x="310" y="{y}" width="38" height="6" rx="3" fill="{c}" opacity=".45"/>' for y in (98, 112, 126))
        return anillos + hoja
    if clave == 'herencia':
        hoja = (f'<path d="M96 60h104v130H96z" fill="{_W}"/><path d="M96 60c-14 0-14 20 0 20M200 190c14 0 14-20 0-20" fill="none" stroke="{_W}" stroke-width="6"/>'
                + ''.join(f'<rect x="112" y="{y}" width="{w}" height="6" rx="3" fill="{c}" opacity=".45"/>' for y, w in ((92, 72), (106, 58), (120, 72), (134, 46)))
                + f'<circle cx="176" cy="164" r="15" fill="{_OC}"/><path d="M168 176l-4 20 12-7 12 7-4-20" fill="{_OC}"/>')
        arbol = (f'<path d="M290 82v30M290 112h-40v26M290 112h40v26M250 160v14M330 160v14M250 174h-18v12M250 174h18v12M330 174h-18v12M330 174h18v12" fill="none" stroke="{_W}" stroke-width="4" opacity=".75"/>'
                 f'<circle cx="290" cy="70" r="15" fill="{_OC}"/><circle cx="250" cy="148" r="12" fill="{_W}"/><circle cx="330" cy="148" r="12" fill="{_W}"/>'
                 + ''.join(f'<circle cx="{x}" cy="194" r="8" fill="{_W}" opacity=".85"/>' for x in (232, 268, 312, 348)))
        return hoja + arbol
    if clave == 'alquiler':
        cartel = (f'<path d="M262 60v120" stroke="{_W}" stroke-width="7" stroke-linecap="round"/><path d="M262 76h70" stroke="{_W}" stroke-width="6" stroke-linecap="round"/>'
                  f'<path d="M282 76v14M322 76v14" stroke="{_W}" stroke-width="3"/><rect x="270" y="90" width="64" height="44" rx="6" fill="{_OC}"/>'
                  f'<circle cx="290" cy="112" r="8" fill="none" stroke="{_W}" stroke-width="4"/><path d="M298 112h22M312 112v8M318 112v6" stroke="{_W}" stroke-width="4" stroke-linecap="round"/>')
        return _casa_ilus(92, 66, 140, c) + cartel
    if clave == 'deudas':
        cal = (f'<rect x="96" y="64" width="128" height="124" rx="10" fill="{_W}"/><rect x="96" y="64" width="128" height="28" rx="10" fill="{_OC}"/><rect x="96" y="82" width="128" height="10" fill="{_OC}"/>'
               f'<path d="M124 54v20M196 54v20" stroke="{_W}" stroke-width="7" stroke-linecap="round"/>'
               + ''.join(f'<rect x="{110 + i * 26}" y="{104 + j * 26}" width="16" height="14" rx="3" fill="{c}" opacity="{.75 if (i, j) == (2, 1) else .3}"/>' for i in range(4) for j in range(3)))
        pct = (f'<circle cx="298" cy="126" r="48" fill="{_OC}"/><path d="M276 152l44-52" stroke="{_W}" stroke-width="8" stroke-linecap="round"/>'
               f'<circle cx="280" cy="108" r="9" fill="none" stroke="{_W}" stroke-width="6"/><circle cx="316" cy="144" r="9" fill="none" stroke="{_W}" stroke-width="6"/>')
        return cal + pct
    if clave == 'juicio':
        mazo = (f'<g transform="rotate(-35 170 110)"><rect x="120" y="86" width="100" height="44" rx="10" fill="{_W}"/>'
                f'<rect x="112" y="80" width="14" height="56" rx="5" fill="{_OC}"/><rect x="214" y="80" width="14" height="56" rx="5" fill="{_OC}"/>'
                f'<rect x="164" y="130" width="14" height="80" rx="6" fill="{_W}"/></g>')
        base = f'<rect x="96" y="182" width="120" height="16" rx="6" fill="{_W}" opacity=".85"/><rect x="110" y="170" width="92" height="14" rx="5" fill="{_OC}"/>'
        hoja = f'<rect x="262" y="66" width="80" height="108" rx="8" fill="{_W}"/>' + ''.join(f'<rect x="276" y="{y}" width="{w}" height="6" rx="3" fill="{c}" opacity=".45"/>' for y, w in ((86, 52), (100, 40), (114, 52), (128, 30))) + f'<circle cx="320" cy="154" r="11" fill="{_OC}"/>'
        return mazo + base + hoja
    if clave == 'cobro':
        hoja = (f'<rect x="100" y="56" width="104" height="136" rx="8" fill="{_W}"/>'
                + ''.join(f'<rect x="116" y="{y}" width="{w}" height="6" rx="3" fill="{c}" opacity=".45"/>' for y, w in ((76, 70), (90, 56), (104, 70), (118, 44)))
                + f'<path d="M116 166h40" stroke="{c}" stroke-width="3" opacity=".6"/><circle cx="178" cy="160" r="16" fill="none" stroke="{_OC}" stroke-width="5"/>')
        mon = ''.join(f'<ellipse cx="{x}" cy="{186 - k * 13}" rx="26" ry="8" fill="{_OC}" stroke="{c}" stroke-opacity=".35" stroke-width="2"/>' for x, n in ((262, 5), (318, 8)) for k in range(n))
        return hoja + mon
    if clave == 'desalojo':
        puerta = f'<rect x="150" y="122" width="40" height="70" rx="3" fill="{c}"/><path d="M150 122l26 8v70l-26-8z" fill="{_OC}"/>'
        flecha = f'<path d="M232 150h86M296 128l24 22-24 22" fill="none" stroke="{_W}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>'
        caja = f'<rect x="300" y="176" width="44" height="22" rx="3" fill="{_OC}" opacity=".9"/>'
        return _casa_ilus(100, 62, 130, c) + puerta + flecha + caja
    if clave == 'contrato':
        h1 = f'<rect x="112" y="52" width="108" height="140" rx="8" fill="{_W}" opacity=".7" transform="rotate(-6 166 122)"/>'
        h2 = f'<rect x="132" y="50" width="108" height="140" rx="8" fill="{_W}"/>' + ''.join(f'<rect x="148" y="{y}" width="{w}" height="6" rx="3" fill="{c}" opacity=".45"/>' for y, w in ((70, 76), (84, 62), (98, 76), (112, 50)))
        firma = f'<path d="M150 164c10-14 18 8 28-4s14 6 24-2" fill="none" stroke="{c}" stroke-width="3"/><path d="M146 176h80" stroke="{c}" stroke-width="2" opacity=".5"/>'
        pluma = f'<g transform="rotate(35 300 120)"><rect x="288" y="56" width="20" height="110" rx="8" fill="{_OC}"/><path d="M288 166h20l-10 22z" fill="{_W}"/></g>'
        return h1 + h2 + firma + pluma
    if clave == 'compraventa':
        etiqueta = (f'<g transform="rotate(14 300 110)"><path d="M262 76h70l20 34-20 34h-70z" fill="{_OC}"/><circle cx="332" cy="110" r="7" fill="{c}"/>'
                    f'<rect x="276" y="98" width="38" height="7" rx="3" fill="{_W}"/><rect x="276" y="114" width="26" height="7" rx="3" fill="{_W}"/></g>')
        hilo = f'<path d="M220 120c20 0 24-10 44-10" fill="none" stroke="{_W}" stroke-width="3"/>'
        return _casa_ilus(84, 66, 140, c) + hilo + etiqueta
    if clave == 'danos':
        vidrio = (f'<rect x="96" y="60" width="140" height="120" rx="6" fill="{_W}"/><rect x="108" y="72" width="116" height="96" fill="{c}" opacity=".25"/>'
                  f'<path d="M166 72l-8 30 22 10-14 26 10 30M158 102l-50 6M180 112l44-14M166 138l-58 20" fill="none" stroke="{_W}" stroke-width="4" stroke-linejoin="round"/>')
        aviso = f'<path d="M300 64l56 100h-112z" fill="{_OC}"/><rect x="295" y="98" width="10" height="36" rx="5" fill="{_W}"/><circle cx="300" cy="148" r="6" fill="{_W}"/>'
        return vidrio + aviso
    # defensa (y valor por defecto): escudo con balanza
    return (f'<path d="M200 40l70 24v58c0 50-34 80-70 94-36-14-70-44-70-94V64z" fill="{_W}"/>'
            f'<path d="M200 74v96M160 92h80M178 182h44" stroke="{c}" stroke-width="7" stroke-linecap="round"/>'
            f'<path d="M160 92l-18 40h36zM240 92l-18 40h36z" fill="none" stroke="{c}" stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="M142 132a18 10 0 0036 0zM222 132a18 10 0 0036 0z" fill="{_OC}"/>'
            f'<path d="M84 196h52M264 196h52" stroke="{_OC}" stroke-width="6" stroke-linecap="round" opacity=".7"/>')


def ilustracion(clave, materia, titulo='', clase='ilus'):
    c = COLOR_MATERIA.get(materia, '#1F5B44')
    aria = f'role="img" aria-label="Ilustración: {E(titulo)}"' if titulo else 'aria-hidden="true"'
    return (f'<svg class="{clase}" viewBox="0 0 400 240" preserveAspectRatio="xMidYMid slice" {aria} xmlns="http://www.w3.org/2000/svg">'
            f'<rect width="400" height="240" fill="{c}"/>'
            f'<circle cx="330" cy="40" r="120" fill="#fff" opacity=".06"/><circle cx="40" cy="230" r="90" fill="#000" opacity=".08"/>'
            f'<path d="{_esc_ilus(226)}" fill="#fff" opacity=".1"/>'
            f'<path d="{_esc_ilus(240, 6, 2)}" fill="{_OC}" opacity=".5"/>'
            f'{_fig_ilus(clave, c)}</svg>')
