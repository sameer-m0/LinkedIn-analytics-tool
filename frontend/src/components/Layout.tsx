import { NavLink, Outlet } from "react-router-dom";
import { DateRangePicker } from "./DateRangePicker";

const NAV = [
  { to: "/", label: "Overview", end: true },
  { to: "/followers", label: "Followers" },
  { to: "/visitors", label: "Visitors" },
  { to: "/content", label: "Content" },
  { to: "/birdseye", label: "Birds Eye View" },
  { to: "/copywriting", label: "Copywriting Lab" },
  { to: "/insights", label: "Insights" },
  { to: "/uploads", label: "Uploads" },
];

export function Layout() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded bg-brand font-bold text-white">in</span>
            <h1 className="text-lg font-semibold text-slate-800">Page Analytics</h1>
          </div>
          <DateRangePicker />
        </div>
        <nav className="mx-auto flex max-w-7xl gap-1 px-6">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                `border-b-2 px-3 py-2 text-sm font-medium transition ${
                  isActive ? "border-brand text-brand" : "border-transparent text-slate-500 hover:text-slate-700"
                }`
              }
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-6">
        <Outlet />
      </main>
    </div>
  );
}
