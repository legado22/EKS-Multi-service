import React from 'react'

const StudentDashboard = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Student Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-2">Enrolled Courses</h3>
          <p className="text-3xl font-bold text-primary-600">5</p>
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold mb-2">Completed</h3>
          <p className="text-3xl font-bold text-green-600">2</p>
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold mb-2">In Progress</h3>
          <p className="text-3xl font-bold text-yellow-600">3</p>
        </div>
      </div>
    </div>
  )
}

export default StudentDashboard