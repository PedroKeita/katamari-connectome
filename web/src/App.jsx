import useSessionData  from './hooks/useSessionData';
import Header          from './components/Header';
import Footer          from './components/Footer';
import VideoPanel      from './components/VideoPanel';
import FlyPanel        from './components/FlyPanel';
import ScienceSections from './components/ScienceSections';
import CollectFlash    from './components/CollectFlash';

export default function App() {
  const { state, connected } = useSessionData('ws://localhost:8765');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>

      {/* ── VISUALIZER — 100vh, grid igual ao original ─────────────── */}
      <div style={{
        height: '100vh',
        display: 'grid',
        gridTemplateRows: '32px 1fr 32px',
        gridTemplateColumns: '1fr 1fr',
        flexShrink: 0,
      }}>
        <Header connected={connected} />
        <VideoPanel state={state} />
        <FlyPanel   state={state} />
        <Footer     state={state} />
      </div>

      {/* ── SCIENCE — scroll normal abaixo ───────────────────────── */}
      <ScienceSections />

      {/* ── FLASH de coleta ─────────────────────────────────────── */}
      <CollectFlash collected={state.collected ?? 0} />
    </div>
  );
}
