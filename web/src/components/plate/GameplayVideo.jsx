import { useEffect, useRef } from 'react';
import { attachVideo, togglePlay } from '../../data/sessionStore';
import { useSession } from '../../hooks';
import styles from './Plate.module.css';

const SRC = `${process.env.PUBLIC_URL || ''}/media/gameplay.mp4`;
const POSTER = `${process.env.PUBLIC_URL || ''}/media/poster.jpg`;

/** Fig. A body. The video is the replay clock (see sessionStore). */
export default function GameplayVideo({ reducedMotion }) {
  const ref = useRef(null);
  const status = useSession((s) => s.videoStatus);

  useEffect(() => attachVideo(ref.current), []);

  return (
    <div className={styles.videoBox}>
      <video
        ref={ref}
        className={styles.video}
        src={SRC}
        poster={POSTER}
        autoPlay={!reducedMotion}
        loop
        muted
        playsInline
        preload="metadata"
        onClick={togglePlay}
        aria-label="Screen capture of Katamari Damacy REROLL being played by the simulated fly brain"
      />
      {status === 'error' && (
        <div className={styles.videoFallback} role="status">
          <p>Gameplay footage is unavailable.</p>
          <p>The recorded signals keep playing on their own clock.</p>
        </div>
      )}
    </div>
  );
}
