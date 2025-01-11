"use client";

import SideBar from "../components/side_bar/side_bar";
import TopBar from "../components/top_bar";
import { useRouter } from "next/navigation";
import { createContext, useEffect, useState } from "react";
import { wrappedFetch } from "../lib/fetch";

interface DataStatus {
  message: string;
  stop_polling: boolean;
}

interface HomeContextType {
  dataStatus: DataStatus;
  setDisabledSidebarSteps: (disabledSidebarSteps: string[]) => void;
  setDataStatus: (dataStatus: DataStatus) => void;
}

export const HomeContext = createContext<HomeContextType>({
  dataStatus: {
    message: "Data status unknown...",
    stop_polling: false,
  },
  setDisabledSidebarSteps: (disabledSidebarSteps) => { },
  setDataStatus: (dataStatus) => { },
});

export default function HomeLayout({ children }: { children: React.ReactNode }) {
  const [sidebarVisible, setSidebarVisible] = useState(false);
  /* Initially all buttons are disabled */
  const [disabledSidebarSteps, setDisabledSidebarSteps] = useState([
    "visualisations",
  ]);

  const [dataStatus, setDataStatus] = useState({
    message: "Data status unknown...",
    stop_polling: false,
  });
  const toggleSidebar = () => {
    setSidebarVisible(!sidebarVisible);
  };

  const router = useRouter();

  function pollDataStatus(
    callback?: () => void
  ) {
    const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    var url = `${apiUrl}/api/data_status`;


    wrappedFetch(
      url,
      (data) => {
        updateDisabledSidebarSteps(data.stop_polling ? [] : ["visualisations"]);
        setDataStatus(data);
        if (!data.stop_polling) {
          // If stop_polling is not true, poll again after 2 seconds
          setTimeout(() => pollDataStatus(callback), 2000);
        } else {
          if (callback) {
            callback();
          }
        }
      },
      (err) => {
        console.log("oopsie, an error happened.");
      },
      router
    );
  }

  function updateDisabledSidebarSteps(
    disabledSidebarSteps: string[]
  ) {
    setDisabledSidebarSteps(disabledSidebarSteps);
  }

  useEffect(() => {
    if (dataStatus.stop_polling == false) {
      pollDataStatus(() => { })
    }
  }, [dataStatus.stop_polling]);

  return (
    <>
      <HomeContext.Provider
        value={{
          dataStatus,
          setDisabledSidebarSteps,
          setDataStatus,
        }}
      >
        <TopBar sidebarVisible={sidebarVisible} toggleSidebar={toggleSidebar} />
        <div className="flex flex-row p-2 gap-2 grow overflow-auto">
          <SideBar
            sidebarVisible={sidebarVisible}
            toggleSidebar={toggleSidebar}
            disabledSidebarSteps={disabledSidebarSteps}
          />
          {/* Content */}
          <div className="flex bg-white rounded-lg p-2 overflow-auto grow justify-center">
            {children}
          </div>
        </div>
      </HomeContext.Provider>
    </>
  );
}
