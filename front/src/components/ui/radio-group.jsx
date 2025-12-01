import React from "react"
import { cn } from "@/lib/utils"

const RadioGroupContext = React.createContext({})

const RadioGroup = React.forwardRef(({ className, value, onValueChange, children, ...props }, ref) => {
    return (
        <RadioGroupContext.Provider value={{ value, onValueChange }}>
            <div className={cn("grid gap-2", className)} role="radiogroup" ref={ref} {...props}>
                {children}
            </div>
        </RadioGroupContext.Provider>
    )
})
RadioGroup.displayName = "RadioGroup"

const RadioGroupItem = React.forwardRef(({ className, value: itemValue, ...props }, ref) => {
    const { value, onValueChange } = React.useContext(RadioGroupContext)
    const checked = value === itemValue

    return (
        <button
            type="button"
            role="radio"
            aria-checked={checked}
            data-state={checked ? "checked" : "unchecked"}
            value={itemValue}
            className={cn(
                "aspect-square h-4 w-4 rounded-full border border-primary text-primary ring-offset-background focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
                checked ? "bg-primary text-primary-foreground" : "bg-transparent",
                className
            )}
            onClick={() => onValueChange(itemValue)}
            ref={ref}
            {...props}
        >
            <span className={cn("flex items-center justify-center", checked ? "block" : "hidden")}>
                <div className="h-2.5 w-2.5 rounded-full bg-current" />
            </span>
        </button>
    )
})
RadioGroupItem.displayName = "RadioGroupItem"

export { RadioGroup, RadioGroupItem }
