import { useSession } from '../../hooks';
import { signed } from '../../data/session';
import styles from './MotorOutput.module.css';

const MOVE = [[null, 'w', null], ['a', 's', 'd']];
const LOOK = [[null, 'i', null], ['j', 'k', 'l']];

function Cluster({ label, rows, keys, escape }) {
  return (
    <div className={styles.cluster}>
      <div className={styles.keys}>
        {rows.flat().map((k, i) =>
          k ? (
            <kbd
              key={k}
              className={styles.key}
              data-on={keys.includes(k) || undefined}
              data-escape={escape || undefined}
            >
              {k.toUpperCase()}
              {keys.includes(k) && <span className="sr-only"> (pressed)</span>}
            </kbd>
          ) : (
            <span key={`gap-${i}`} aria-hidden="true" />
          ),
        )}
      </div>
      <span className={styles.clusterLabel}>{label}</span>
    </div>
  );
}

function FieldBar({ label, value }) {
  const v = Math.max(0, Math.min(1, value));
  return (
    <div className={styles.field}>
      <div className={styles.fieldTrack}>
        <div className={styles.fieldFill} style={{ transform: `scaleY(${v})` }} />
      </div>
      <span className={`mono ${styles.fieldVal}`}>{value.toFixed(2)}</span>
      <span className={styles.fieldLabel}>{label}</span>
    </div>
  );
}

/** Fig. D — what the descending neurons are doing to the keyboard right now. */
export default function MotorOutput() {
  const keys = useSession((s) => s.frame.pressed_keys);
  const escape = useSession((s) => s.frame.escape_active);
  const left = useSession((s) => s.frame.left);
  const center = useSession((s) => s.frame.center);
  const right = useSession((s) => s.frame.right);
  const bias = useSession((s) => s.frame.fw_bias);
  const mag = useSession((s) => s.frame.mag);

  const b = Math.max(-1, Math.min(1, bias));
  const m = Math.max(0, Math.min(1, mag));

  return (
    <div className={styles.motor}>
      <div className={styles.keyboard} role="group" aria-label="Keys being pressed">
        <Cluster label="Move" rows={MOVE} keys={keys} />
        <Cluster label="Camera" rows={LOOK} keys={keys} />
        <div className={styles.mods}>
          {['shift', 'ctrl'].map((k) => (
            <kbd
              key={k}
              className={`${styles.key} ${styles.wide}`}
              data-on={keys.includes(k) || undefined}
              data-escape={escape || undefined}
            >
              {k.toUpperCase()}
              {keys.includes(k) && <span className="sr-only"> (pressed)</span>}
            </kbd>
          ))}
          <span className={styles.clusterLabel} data-alert={escape || undefined}>
            {escape ? 'Escape firing' : 'Escape'}
          </span>
        </div>
      </div>

      <div className={styles.signals}>
        <div className={styles.fieldGroup} role="group" aria-label="Visual field input: left, centre, right">
          <FieldBar label="L" value={left} />
          <FieldBar label="C" value={center} />
          <FieldBar label="R" value={right} />
          <span className={styles.groupLabel}>Visual field</span>
        </div>

        <div className={styles.meters}>
          <div className={styles.meter}>
            <div className={styles.meterHead}>
              <span>Steering bias</span>
              <span className={`mono ${styles.meterVal}`}>{signed(bias, 3)}</span>
            </div>
            <div className={styles.biasTrack} aria-hidden="true">
              <span className={styles.biasMid} />
              {/* Compositor-only: fill scales from centre (negative = leftwards), needle translates. */}
              <span
                className={styles.biasFill}
                style={{ transform: `scaleX(${b})` }}
                data-side={b < 0 ? 'l' : 'r'}
              />
              <span className={styles.needleRail} style={{ transform: `translateX(${b * 50}%)` }}>
                <span className={styles.needle} />
              </span>
            </div>
            <div className={styles.meterScale} aria-hidden="true"><span>← left</span><span>right →</span></div>
          </div>

          <div className={styles.meter}>
            <div className={styles.meterHead}>
              <span>Motor drive</span>
              <span className={`mono ${styles.meterVal}`}>{mag.toFixed(2)}</span>
            </div>
            <div className={styles.driveTrack} aria-hidden="true">
              <span className={styles.driveFill} style={{ transform: `scaleX(${m})` }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
