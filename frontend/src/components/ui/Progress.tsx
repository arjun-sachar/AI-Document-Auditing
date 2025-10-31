import React from 'react'
import { cn } from '@/lib/utils'

interface ProgressProps {
  value: number
  max?: number
  className?: string
  showPercentage?: boolean
  size?: 'sm' | 'md' | 'lg'
  color?: 'default' | 'success' | 'warning' | 'error'
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ 
    value, 
    max = 100, 
    className, 
    showPercentage = true,
    size = 'md',
    color = 'default',
    ...props 
  }, ref) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100)
    
    const sizeClasses = {
      sm: 'h-2',
      md: 'h-3',
      lg: 'h-4',
    }
    
    const colorClasses = {
      default: 'bg-primary',
      success: 'bg-green-500',
      warning: 'bg-yellow-500',
      error: 'bg-red-500',
    }
    
    return (
      <div className={cn('w-full', className)} {...props}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Progress</span>
          {showPercentage && (
            <span className="text-sm text-gray-500">{Math.round(percentage)}%</span>
          )}
        </div>
        <div
          ref={ref}
          className={cn(
            'w-full bg-gray-200 rounded-full overflow-hidden',
            sizeClasses[size]
          )}
        >
          <div
            className={cn(
              'h-full transition-all duration-300 ease-in-out rounded-full',
              colorClasses[color]
            )}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    )
  }
)
Progress.displayName = 'Progress'

export { Progress }

