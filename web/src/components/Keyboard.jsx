const KEY_STYLE = {
  base: {
    width: 44, height: 44, borderRadius: 6,
    background: '#080e14', border: '1px solid var(--border)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: 12, color: 'var(--text-dim)',
    transition: 'all 0.07s', position: 'relative',
    userSelect: 'none', cursor: 'default',
    flexShrink: 0,
  },
  on: {
    background: '#0a1e14', borderColor: 'var(--green)',
    color: 'var(--green-bright)', boxShadow: '0 0 14px #4caf8722',
    transform: 'translateY(2px)',
  },
  escape: {
    background: '#1a0a0a', borderColor: 'var(--red-bright)',
    color: 'var(--red-bright)', boxShadow: '0 0 14px #e0555522',
    transform: 'translateY(2px)',
  },
  wide: { width: 72 },
  gap: { visibility: 'hidden' },
};

function Key({ id, label, pressed, escape }) {
  const active = pressed;
  const style  = {
    ...KEY_STYLE.base,
    ...(id === 'ctrl' || id === 'shift' ? KEY_STYLE.wide : {}),
    ...(active && escape ? KEY_STYLE.escape : {}),
    ...(active && !escape ? KEY_STYLE.on : {}),
  };
  return (
    <div style={style}>
      {label ?? id.toUpperCase()}
      <div style={{
        position: 'absolute', bottom: 4, left: '50%',
        transform: 'translateX(-50%)',
        width: id === 'ctrl' || id === 'shift' ? 48 : 26,
        height: 2, borderRadius: 1,
        background: active ? (escape ? '#e0555544' : '#4caf8744') : 'var(--border)',
        transition: 'background 0.07s',
      }} />
    </div>
  );
}

function Gap() {
  return <div style={{ ...KEY_STYLE.base, ...KEY_STYLE.gap }} />;
}

export default function Keyboard({ pressedKeys = [], escapeActive = false }) {
  const has = (k) => pressedKeys.includes(k);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 5, alignItems: 'center' }}>
      {/* Row 1: W / I */}
      <div style={{ display: 'flex', gap: 5 }}>
        <Gap />
        <Key id="w" pressed={has('w')} />
        <Gap />
        <div style={{ width: 16 }} />
        <Gap />
        <Key id="i" pressed={has('i')} />
        <Gap />
      </div>

      {/* Row 2: ASDF / JKIL */}
      <div style={{ display: 'flex', gap: 5 }}>
        <Key id="a" pressed={has('a')} />
        <Key id="s" pressed={has('s')} />
        <Key id="d" pressed={has('d')} />
        <div style={{ width: 16 }} />
        <Key id="j" pressed={has('j')} />
        <Key id="k" pressed={has('k')} />
        <Key id="l" pressed={has('l')} />
      </div>

      {/* Row 3: CTRL + SHIFT */}
      <div style={{ display: 'flex', gap: 5, marginTop: 2 }}>
        <Key id="ctrl"  label="CTRL"  pressed={has('ctrl')}  escape={escapeActive} />
        <div style={{ width: 16 }} />
        <Key id="shift" label="SHIFT" pressed={has('shift')} escape={escapeActive} />
      </div>

      {/* Labels */}
      <div style={{
        display: 'flex', justifyContent: 'space-around', width: '100%',
        fontSize: 9, color: 'var(--text-dim)', letterSpacing: 2, marginTop: 2,
      }}>
        <span>LEFT STICK</span>
        <span>RIGHT STICK</span>
      </div>
    </div>
  );
}
