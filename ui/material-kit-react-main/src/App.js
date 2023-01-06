import { getFirestore } from 'firebase/firestore';
import { FirestoreProvider, useFirebaseApp } from 'reactfire';
import { StyledChart } from './components/chart';
import ScrollToTop from './components/scroll-to-top';
import Router from './routes';
import ThemeProvider from './theme';

// ----------------------------------------------------------------------

export default function App() {
    const firestoreInstance = getFirestore(useFirebaseApp());
    return (
        <FirestoreProvider sdk={firestoreInstance}>
            <ThemeProvider>
                <ScrollToTop />
                <StyledChart />
                <Router />
            </ThemeProvider>
        </FirestoreProvider>
    );
}
