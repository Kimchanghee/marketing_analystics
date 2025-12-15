export default function TestPage() {
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-4xl font-bold text-blue-600 mb-4">Tailwind CSS Test</h1>
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Card 1</h2>
          <p className="text-gray-600">This is a test card with Tailwind classes.</p>
        </div>
        <div className="bg-red-100 p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold text-red-800 mb-2">Card 2</h2>
          <p className="text-red-600">This card has red background.</p>
        </div>
        <div className="bg-green-100 p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold text-green-800 mb-2">Card 3</h2>
          <p className="text-green-600">This card has green background.</p>
        </div>
      </div>
      <div className="mt-8">
        <button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
          Test Button
        </button>
        <button className="ml-4 bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded">
          Secondary Button
        </button>
      </div>
    </div>
  );
}