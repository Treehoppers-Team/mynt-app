import React, { useState } from "react";
import axios from "axios";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

interface TableRow {
  id: string;
  name: string;
  handle: string;
  number: number;
  status: "SUCCESSFUL" | "REDEEMED" | "UNSUCCESSFUL" | "PENDING";
  verification: "VERIFIED" | "UNVERIFIED" | "REJECTED";
  mint_account: string;
  registration_time: string;
  redemption_time: string;
}

interface Event {
  capacity: string;
  description: string;
  eventType: string;
  imageCID: string;
  price: number;
  symbol: string;
  time: string;
  title: string;
  venue: string;
}

interface TableProps {
  data: TableRow[];
  event: Event;
}

const Table: React.FC<TableProps> = ({ data, event }) => {
  const [sortColumn, setSortColumn] = useState<string>("name");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const [selectedRows, setSelectedRows] = useState<string[]>([]);
  const [selectAll, setSelectAll] = useState(false);
  const [showOptions, setShowOptions] = useState(false);

  const sortedData = data.sort((a, b) => {
    const aValue = a[sortColumn as keyof TableRow];
    const bValue = b[sortColumn as keyof TableRow];
    if (aValue < bValue) {
      return sortDirection === "asc" ? -1 : 1;
    }
    if (aValue > bValue) {
      return sortDirection === "asc" ? 1 : -1;
    }
    return 0;
  });

  const handleSort = (column: string) => {
    if (column === sortColumn) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }
  };

  const handleRowSelect = (registrationId: string) => {
    if (selectedRows.includes(registrationId)) {
      setSelectedRows(selectedRows.filter((userId) => userId !== registrationId));
    } else {
      setSelectedRows([...selectedRows, registrationId]);
    }
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedRows([]);
    } else {
      const allRowIds = data.map((row: { id: any; }) => row.id);
      setSelectedRows(allRowIds);
    }
    setSelectAll(!selectAll);
  };

  const handleOptionsClick = () => {
    setShowOptions(!showOptions);
  };

  const handleVerify = () => {
    console.log("This is the handle verify button")
    console.log(selectedRows)
    let counter = 0;

      for (let i = 0; i < selectedRows.length; i++) {
        console.log(selectedRows[i])
        const registrationData = {
          user_id: selectedRows[i],
          event_title: event.title,
          status: "SUCCESSFUL",
          verification: "VERIFIED",
        };
        axios
          .post(BASE + "/updateRegistration", registrationData)
          .then((response: { data: any }) => {
            console.log(response.data);
            counter += 1;
          })
          .then(() => {
            if (counter === selectedRows.length) {
              console.log("verification updated");
              window.location.reload();
            }
          });
      }
  };
  
  const handleReject = () => {
    console.log("This is the handle rejected button")
    console.log(selectedRows)
    let counter = 0;

      for (let i = 0; i < selectedRows.length; i++) {
        console.log(selectedRows[i])
        const registrationData = {
          user_id: selectedRows[i],
          event_title: event.title,
          status: "UNSUCCESSFUL",
          verification: "REJECTED",
        };
        axios
          .post(BASE + "/updateRegistration", registrationData)
          .then((response: { data: any }) => {
            console.log(response.data);
            counter += 1;
          })
          .then(() => {
            if (counter === selectedRows.length) {
              console.log("verification updated");
              window.location.reload();
            }
          });
      }
  };

  return (
    <div className="overflow-x-auto rounded-lg m-4">
      <table className="w-full table-auto border-collapse">
        <thead className="text-black bg-gray-100">
          <tr>
            <th className="px-4 py-2">
              <input
                type="checkbox"
                checked={selectAll}
                onChange={handleSelectAll}
              />
            </th>
            <th className="px-4 py-2">#</th>
            <th className="px-4 py-2" onClick={() => handleSort("name")}>
              Name{" "}
              {sortColumn === "name" && (sortDirection === "asc" ? "▲" : "▼")}
            </th>
            <th className="px-4 py-2" onClick={() => handleSort("status")}>
              Status{" "}
              {sortColumn === "status" && (sortDirection === "asc" ? "▲" : "▼")}
            </th>
            <th className="px-4 py-2" onClick={() => handleSort("verification")}>
              Verification{" "}
              {sortColumn === "status" && (sortDirection === "asc" ? "▲" : "▼")}
            </th>
            <th className="px-4 py-2" onClick={() => handleSort("handle")}>
              Handle{" "}
              {sortColumn === "handle" && (sortDirection === "asc" ? "▲" : "▼")}
            </th>
            <th className="px-4 py-2" onClick={() => handleSort("number")}>
              Number{" "}
              {sortColumn === "number" && (sortDirection === "asc" ? "▲" : "▼")}
            </th>

            <th className="px-4 py-2" onClick={() => handleSort("status")}>
              NFT{" "}
              {sortColumn === "status" && (sortDirection === "asc" ? "▲" : "▼")}
            </th>

            <th
              className="px-4 py-2"
              onClick={() => handleSort("registration_time")}
            >
              Registration Time{" "}
              {sortColumn === "registation_time" &&
                (sortDirection === "asc" ? "▲" : "▼")}
            </th>

            <th
              className="px-4 py-2"
              onClick={() => handleSort("redemption_time")}
            >
              Redemption Time{" "}
              {sortColumn === "redemption_time" &&
                (sortDirection === "asc" ? "▲" : "▼")}
            </th>
            <th className="px-4 py-2">
            <div className="flex justify-end">
              <button
                onClick={handleOptionsClick}
                className="p-2 focus:outline-none hover:bg-gray-300 rounded-md"
              >
                ⋮
              </button>
            </div>
            {showOptions && (
              <div className="absolute bg-white p-2 shadow-md">
                <button onClick={() => handleVerify()}>Verify</button>
                <button onClick={() => handleReject()}>Reject</button>
              </div>
            )}
          </th>
          </tr>
        </thead>
        <tbody className="text-gray-700">
          {sortedData.map((row, index) => (
            <tr key={index}>
              <td className="border px-4 py-2">
                <input
                  type="checkbox"
                  checked={selectedRows.includes(row.id)}
                  onChange={() => handleRowSelect(row.id)}
                />
              </td>
              <td className="border px-4 py-2">{index + 1}</td>
              <td className="border px-4 py-2">{row.name}</td>
              <td className="border px-4 py-2">
                <span
                  className={`${
                    row.status === "REDEEMED"
                      ? "bg-green-500"
                      : row.status === "SUCCESSFUL"
                      ? "bg-blue-500"
                      : row.status === "UNSUCCESSFUL"
                      ? "bg-red-500"
                      : row.status === "PENDING"
                      ? "bg-yellow-500"
                      : ""
                  } text-white py-1 px-2 rounded-full`}
                >
                  {row.status}
                </span>
              </td>
              <td className="border px-4 py-2">
                <span
                  className={`${
                    row.verification === "VERIFIED"
                      ? "bg-blue-500"
                      : row.verification === "REJECTED"
                      ? "bg-red-500"
                      : row.verification === "UNVERIFIED"
                      ? "bg-yellow-500"
                      : ""
                  } text-white py-1 px-2 rounded-full`}
                >
                  {row.verification}
                </span>
              </td>
              <td className="border px-4 py-2">
                <a
                  href={`https://t.me/${row.handle}`}
                  className="font-light hover:text-blue-500"
                >
                  @{row.handle}
                </a>
              </td>

              <td className="border px-4 py-2">
                <a
                  className="font-light hover:text-blue-500"
                  href={`tel:{row.number}`}
                >
                  {row.number}
                </a>
              </td>

              <td className="border px-4 py-2">
                <a>
                  {row.mint_account !== "N/A" && row.mint_account !== "Minting failed" ? (
                    <a
                      href={`https://solana.fm/address/${row.mint_account}/metadata?cluster=devnet-qn1`}
                      className="flex flex-wrap font-light hover:text-blue-500"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke-width="1.5"
                        stroke="currentColor"
                        className="w-6 h-6 mr-1"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244"
                        />
                      </svg>
                      Ticket Link
                    </a>
                  ) : null}
                </a>
                {row.mint_account === "Minting failed" ? (
                  <a style={{ color: "red" }}>Minting failed</a>
                ) : null}
              </td>

              <td className="border px-4 py-2">
                <a>{row.registration_time}</a>
              </td>

              <td className="border px-4 py-2">
                <a>{row.redemption_time}</a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Table;
