import { useEffect } from 'react';
import { start } from './data/sessionStore';
import Masthead from './components/layout/Masthead';
import SiteFooter from './components/layout/SiteFooter';
import Plate from './components/plate/Plate';
import Method from './components/acts/Method';
import Circuits from './components/acts/Circuits';
import RunIt from './components/acts/RunIt';

/**
 * Four acts on one page: claim and evidence (Plate), method, circuits, reproduce.
 * Only small leaf components subscribe to the session store, so neural ticks
 * never re-render the page tree.
 */
export default function App() {
  useEffect(() => start(), []);

  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>
      <div id="top" />
      <Masthead />
      <main id="main">
        <Plate />
        <Method />
        <Circuits />
        <RunIt />
      </main>
      <SiteFooter />
    </>
  );
}
