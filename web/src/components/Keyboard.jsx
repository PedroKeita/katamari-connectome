const BASE = {
  width: 44, height: 44, borderRadius: 6,
  background: '#2a1820', border: '1px solid var(--border)',
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  fontSize: 12, color: 'var(--text-dim)',
  transition: 'all 0.07s', position: 'relative',
  userSelect: 'none', cursor: 'default',
  flexShrink: 0,
};

const ON = {
  background: '#3d1030',
  borderColor: 'var(--magenta)',
  color: '#ff80b8',
  boxShadow: '0 0 14px rgba(255,63,142,0.2)',
  transform: 'translateY(2px)',
};

const ESC = {
  background: '#3d1a14',
  borderColor: 'var(--coral)',
  color: 'var(--coral)',
  boxShadow: '0 0 14px rgba(255,90,78,0.2)',
  transform: 'translateY(2px)',
};

const WIDE = { width: 72 };
const HIDDEN = { visibility: 'hidden' };

function Key({ id, label, pressed, escape }) {
  const style = {
    ...BASE,
    ...(id === 'ctrl' || id === 'shift' ? WIDE : {}),
    ...(pressed && escape  ? ESC : {}),
    ...(pressed && !escape ? ON  : {}),
  };

  const barW = id === 'ctrl' || id === 'shift' ? 48 : 26;
  const barColor = pressed
    ? escape ? 'rgba(255,90,78,0.35)' : 'rgba(255,63,142,0.35)'
    : 'var(--border)';

  return (
    <div style={style}>
      {label ?? id.toUpperCase()}
      <div style={{
        position: 'absolute', bottom: 4, left: '50%',
        transform: 'translateX(-50%)',
        width: barW, height: 2, borderRadius: 1,
        background: barColor, transition: 'background 0.07s',
      }} />
    </div>
  );
}

function Gap() {
  return <div style={{ ...BASE, ...HIDDEN }} />;
}

export default function Keyboard({ pressedKeys = [], escapeActive = false }) {
  const has = (k) => pressedKeys.includes(k);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 5, alignItems: 'center' }}>
      {/* Row 1 */}
      <div style={{ display: 'flex', gap: 5 }}>
        <Gap />
        <Key id="w" pressed={has('w')} />
        <Gap />
        <div style={{ width: 16 }} />
        <Gap />
        <Key id="i" pressed={has('i')} />
        <Gap />
      </div>

      {/* Row 2 */}
      <div style={{ display: 'flex', gap: 5 }}>
        <Key id="a" pressed={has('a')} />
        <Key id="s" pressed={has('s')} />
        <Key id="d" pressed={has('d')} />
        <div style={{ width: 16 }} />
        <Key id="j" pressed={has('j')} />
        <Key id="k" pressed={has('k')} />
        <Key id="l" pressed={has('l')} />
      </div>

      {/* Row 3 */}
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