import PanelLabel from './PanelLabel';
import FlyBody3D   from './FlyBody3D';
import Keyboard    from './Keyboard';
import BiasBar     from './BiasBar';

export default function FlyPanel({ state }) {
  return (
    <div style={{ position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <PanelLabel left="02 / FLY RIG" right="Flybody anatomical · Three.js" />

      {/* 3D fly — takes upper ~55% */}
      <div style={{ flex: '0 0 55%', paddingTop: 28, minHeight: 0 }}>
        <FlyBody3D state={state} />
      </div>

      {/* Keyboard + bias — lower area */}
      <div style={{
        flex: 1, borderTop: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        gap: 14, padding: '12px 20px 16px',
      }}>
        <div style={{ fontSize: 9, color: 'var(--text-dim)', letterSpacing: 2, alignSelf: 'flex-start' }}>
          03 / KEYBOARD OUTPUT
        </div>
        <Keyboard
          pressedKeys={state.pressed_keys ?? []}
          escapeActive={state.escape_active ?? false}
        />
        <BiasBar
          bias={state.fw_bias    ?? 0}
          left={state.left       ?? 0}
          center={state.center   ?? 0}
          right={state.right     ?? 0}
          collected={state.collected ?? 0}
        />
      </div>
    </div>
  );
}
