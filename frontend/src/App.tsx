import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { RangeProvider } from "./hooks/useRange";
import { BirdsEyePage } from "./pages/BirdsEyePage";
import { CopywritingLabPage } from "./pages/CopywritingLabPage";
import { ContentPage } from "./pages/ContentPage";
import { FollowersPage } from "./pages/FollowersPage";
import { InsightsPage } from "./pages/InsightsPage";
import { OverviewPage } from "./pages/OverviewPage";
import { UploadsPage } from "./pages/UploadsPage";
import { VisitorsPage } from "./pages/VisitorsPage";

export default function App() {
  return (
    <RangeProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<OverviewPage />} />
            <Route path="followers" element={<FollowersPage />} />
            <Route path="visitors" element={<VisitorsPage />} />
            <Route path="content" element={<ContentPage />} />
            <Route path="birdseye" element={<BirdsEyePage />} />
            <Route path="copywriting" element={<CopywritingLabPage />} />
            <Route path="insights" element={<InsightsPage />} />
            <Route path="uploads" element={<UploadsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </RangeProvider>
  );
}
