"use client";
import { useState } from "react";
import { SummaryCard } from "@/app/admin/components/Components";
import { ChartBarDefault, type GraphProps } from "@/app/admin/components/Graph";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import {
  ButtonGroup,
  ButtonGroupSeparator,
  ButtonGroupText,
} from "@/components/ui/button-group"
import { Button } from "@/components/ui/button";


type DashboardItem = {
  type: string;
  width?: string;
  x?: string;
  y?: string;
};

type SelectedMode = "branch" | "priority" | "sla";

export default function Homepage({ items = [] }: { items?: DashboardItem[] }) {
  const [selectedMode, setSelectedMode] = useState<SelectedMode>("branch");

  // Sample branch data for the chart
  const branchData = [
    { name: "Branch A", jobsCompleted: 45 },
    { name: "Branch B", jobsCompleted: 38 },
    { name: "Branch C", jobsCompleted: 52 },
    { name: "Branch D", jobsCompleted: 41 },
    { name: "Branch E", jobsCompleted: 35 },
  ];

  return (
     <main className="z-10 fixed left-0 pl-[calc((25%)+(var(--spacing)*6))] overflow-x-hidden right-0 bottom-0 top-0 p-4 pt-18 overflow-y-auto flex flex-col gap-4">
      <div className="-ml-[calc((25%)+(var(--spacing)*4))] pl-[calc((25%)+(var(--spacing)*4))] -mr-8 pr-8 h-1/5 shrink-0 no-scrollbar flex flex-row overflow-x-auto gap-2">
        <SummaryCard description="Jobs Today" type="number" value={50} />
        <SummaryCard description="Active Technicians" type="number" value={12} />
        <SummaryCard description="SLA Compliance" type="percent" value={92} />
        <SummaryCard description="Overdue Jobs" type="number" value={3} />
      </div>
  <div className="h-[calc(80%-(var(--spacing)*4))] shrink-0 bg-primary w-full rounded-md overflow-hidden">
        <div className="flex flex-row px-2 gap-2 items-center h-12">
          <Select>
			<SelectTrigger className="w-36 bg-secondary">
				<SelectValue placeholder="Time" />
			</SelectTrigger>
			<SelectContent>
				<SelectItem className="cursor-pointer" value="all-time">All Time</SelectItem>
				<SelectItem className="cursor-pointer" value="year">Year</SelectItem>
				<SelectItem className="cursor-pointer" value="month">Month</SelectItem>
				<SelectItem className="cursor-pointer" value="week">Week</SelectItem>
				<SelectItem className="cursor-pointer" value="day">Day</SelectItem>
				<SelectItem className="cursor-pointer" value="hour">Hour</SelectItem>
			</SelectContent>
			</Select>
			<Select>
				<SelectTrigger className="w-36 bg-secondary">
				<SelectValue placeholder="Time" />
			</SelectTrigger>
          <SelectContent>
				<SelectItem className="cursor-pointer" value="all">All</SelectItem>
				<SelectItem className="cursor-pointer" value="branch-a">Branch A</SelectItem>
				<SelectItem className="cursor-pointer" value="branch-b">Branch B</SelectItem>
				<SelectItem className="cursor-pointer" value="branch-c">Branch C</SelectItem>
				<SelectItem className="cursor-pointer" value="branch-d">Branch D</SelectItem>
			</SelectContent>
			</Select>
          <ButtonGroup className="ml-auto">
			<Button 
              variant={selectedMode === "branch" ? "default" : "outline"} 
              size="sm"
              onClick={() => setSelectedMode("branch")}
            >
              Branch
            </Button>
			<Button 
              variant={selectedMode === "priority" ? "default" : "outline"} 
              size="sm"
              onClick={() => setSelectedMode("priority")}
            >
              Priority
            </Button>
			<Button 
              variant={selectedMode === "sla" ? "default" : "outline"} 
              size="sm"
              onClick={() => setSelectedMode("sla")}
            >
              SLA
            </Button>
		</ButtonGroup>
        </div>
        {selectedMode === "branch" && (
          <div className="h-full overflow-hidden">
            <ChartBarDefault
              title="Jobs Completed by Branch"
              description="Number of jobs completed per branch"
              chartData={branchData}
              dataKey="jobsCompleted"
              footerText="Based on current period"
              trendingUp={true}
              trendingPercent={12}
            />
          </div>
        )}
      </div>
  <div className="h-full flex flex-row gap-4">
  <div className="w-2/3 h-72 bg-primary p-2 flex flex-col rounded-md overflow-hidden">
        <div className="flex flex-row px-2 items-center h-12">
          <h3 className="font-bold text-2xl">Live Jobs</h3>
        </div>
        <ul className="flex flex-col h-full pt-2 px-2">
          <li className="cursor-pointer hover:bg-secondary/70 px-2 rounded-sm transition-colors w-full flex flex-row items-center h-10">
            <p>HVAC out of date</p>
            <div className="h-6 ml-auto bg-destructive/75 border-2 border-destructive-border flex flex-row items-center px-1 rounded-xs">
              <p className="text-sm text-destructive-text">Urgent</p>
            </div>
          </li>
          <li className="cursor-pointer hover:bg-secondary/70 px-2 rounded-sm transition-colors w-full flex flex-row items-center h-10">
            <p>Appliance check-up</p>
            <div className="h-6 ml-auto bg-warning/80 border-2 border-warning-border flex flex-row items-center px-1 rounded-xs">
              <p className="text-sm text-warning-text">Assigned</p>
            </div>
          </li>
          <li className="cursor-pointer hover:bg-secondary/70 px-2 rounded-sm transition-colors w-full flex flex-row items-center h-10">
            <p>Appliance problem</p>
            <div className="h-6 ml-auto bg-success/80 border-2 border-success-border flex flex-row items-center px-1 rounded-xs">
              <p className="text-sm text-success-text">In Progress</p>
            </div>
          </li>
        </ul>
      </div>
      <div className="w-1/3 h-72 bg-primary p-2 flex flex-col rounded-md overflow-hidden">
        <div className="flex flex-row px-2 items-center h-12">
          <h3 className="font-bold text-2xl">Top Techs</h3>
        </div>
        <ul className="flex flex-col h-full pt-2 px-2">
          <li className="cursor-pointer hover:bg-secondary/70 px-2 rounded-sm transition-colors w-full flex flex-row items-center h-10">
            <p>Tanay Shah</p>
          </li>
          <li className="cursor-pointer hover:bg-secondary/70 px-2 rounded-sm transition-colors w-full flex flex-row items-center h-10">
            <p>Aiden Santiago</p>
          </li>
          <li className="cursor-pointer hover:bg-secondary/70 px-2 rounded-sm transition-colors w-full flex flex-row items-center h-10">
            <p>Badri I'm not spelling</p>
          </li>
        </ul>
      </div>
      </div>
    </main>
  );
}

